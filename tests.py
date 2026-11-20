import unittest
import base64
import io
import os
from unittest.mock import patch, MagicMock
from PIL import Image
from app import app, ADMIN_CODE
from challenges import OFFICIAL_CATEGORIES, challenge_manager
from evaluation import ai_evaluator, validate_prompt_anti_cheat
from image_generator import image_generator


def _make_sample_jpeg_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color=(180, 40, 40)).save(buf, format="JPEG")
    return buf.getvalue()


def _make_sample_jpeg_b64():
    return base64.b64encode(_make_sample_jpeg_bytes()).decode("utf-8")


class TestReversePromptBattle(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_anti_cheat_validator(self):
        # Rule 5: No user should have a prompt like "generate an image like the one on screen"
        cheat_prompts = [
            "generate a image like the one on screen",
            "generate an image like the one on screen",
            "make it identical to the picture on screen",
            "just copy the target image on screen",
            "recreate the image on screen please",
            "same as the picture above",
            "duplicate the screen image",
            "show me the same visual on screen"
        ]
        for p in cheat_prompts:
            is_valid, msg = validate_prompt_anti_cheat(p)
            self.assertFalse(is_valid, f"Failed to catch cheat prompt: '{p}'")
            self.assertIn("Cheating", msg)

        # Valid descriptive visual prompts must pass
        valid_prompts = [
            "A biophilic vertical skyscraper with cascading mist waterfalls and glowing skybridges at dusk, 8k render",
            "Bioluminescent research pods floating on an azure mountain lake at sunrise, octane volumetric lighting",
            "Autonomous solarpunk hydrofoil vessel skimming across coral reef waters in clear daylight"
        ]
        for vp in valid_prompts:
            is_valid, msg = validate_prompt_anti_cheat(vp)
            self.assertTrue(is_valid, f"Falsely rejected valid prompt: '{vp}' - {msg}")

    def test_unique_target_challenge_generation(self):
        # Rule 3: Each user should have a unique image given with zero repetitions
        seen_ids = set()
        for i in range(10):
            t = challenge_manager.get_unique_target_challenge(participant_id=f"user-unique-{i}")
            self.assertIsNotNone(t.get("image_data"))
            self.assertTrue(t.get("title"))
            self.assertNotIn(t["id"], seen_ids, f"Repetition detected for {t['id']}!")
            seen_ids.add(t["id"])

        # Also test sequential rerolls for the same user
        reroll_seen = set()
        single_user = "persistent-tester"
        for i in range(8):
            t = challenge_manager.get_unique_target_challenge(participant_id=single_user, exclude_ids=list(reroll_seen))
            self.assertNotIn(t["id"], reroll_seen, f"Reroll repetition detected: {t['id']}")
            reroll_seen.add(t["id"])

    def test_cloudflare_worker_generator_binary_and_json(self):
        # Verify raw binary JPEG response from saurav-z/free-image-generation-api worker.js
        sample_bytes = _make_sample_jpeg_bytes()
        sample_b64 = base64.b64encode(sample_bytes).decode("utf-8")

        mock_bin_resp = MagicMock()
        mock_bin_resp.status_code = 200
        mock_bin_resp.headers = {"Content-Type": "image/jpeg"}
        mock_bin_resp.content = sample_bytes

        exact_prompt = "A bright red Ferrari parked inside a white showroom with dark shadows"
        worker_url = "https://my-img-worker.example.workers.dev"
        worker_key = "super-secret-worker-key"

        with patch("image_generator.requests.post", return_value=mock_bin_resp) as mock_post, \
             patch.object(image_generator, "_get_worker_config", return_value=(worker_url, worker_key)):
            res = image_generator.generate(exact_prompt)

        self.assertTrue(res["success"])
        self.assertEqual(res["source"], "cloudflare-workers-ai")
        self.assertEqual(res["image_data"], f"data:image/jpeg;base64,{sample_b64}")

        # Rule 4: Verify exact unmodified prompt & Bearer auth sent to Cloudflare Worker
        self.assertEqual(mock_post.call_args[0][0], worker_url)
        self.assertEqual(mock_post.call_args[1]["headers"]["Authorization"], f"Bearer {worker_key}")
        self.assertEqual(mock_post.call_args[1]["json"], {"prompt": exact_prompt})

        # Verify JSON base64 response support (e.g. FLUX on Cloudflare Workers AI)
        mock_json_resp = MagicMock()
        mock_json_resp.status_code = 200
        mock_json_resp.headers = {"Content-Type": "application/json"}
        mock_json_resp.content = b'{"image":"..."}'
        mock_json_resp.json.return_value = {
            "image": sample_b64,
            "model": "@cf/black-forest-labs/flux-1-schnell"
        }

        with patch("image_generator.requests.post", return_value=mock_json_resp), \
             patch.object(image_generator, "_get_worker_config", return_value=(worker_url, worker_key)):
            res_flux = image_generator.generate(exact_prompt)

        self.assertTrue(res_flux["success"])
        self.assertEqual(res_flux["source"], "cloudflare-flux")
        self.assertEqual(res_flux["image_data"], f"data:image/jpeg;base64,{sample_b64}")

        # Verify clean error when CF_WORKER_URL / CF_WORKER_API_KEY are missing
        with patch.object(image_generator, "_get_worker_config", return_value=("", "")):
            res_missing = image_generator.generate(exact_prompt)
        self.assertFalse(res_missing["success"])
        self.assertIn("CF_WORKER_URL", res_missing["error"])

    def test_end_to_end_reverse_prompt_workflow(self):
        # 1. User joins on Identifier page with Name & Email
        join_resp = self.client.post('/api/join', json={
            'name': 'Sarah Connor',
            'email': 'sarah@resistance.edu'
        })
        self.assertEqual(join_resp.status_code, 200)
        join_data = join_resp.get_json()
        self.assertTrue(join_data['success'])
        self.assertEqual(join_data['timer_duration'], 180)
        pid = join_data['participant']['id']
        target_challenge = join_data['target_challenge']

        # Ensure target image is present
        self.assertIn('image_data', target_challenge)
        self.assertTrue(len(target_challenge['image_data']) > 100)

        # Ensure hidden_prompt is NOT sent to client
        self.assertNotIn('hidden_prompt', target_challenge)

        # 2. Test Anti-Cheat Rejection via API (does not burn attempt on manual click)
        cheat_resp = self.client.post('/api/generate', json={
            'participant_id': pid,
            'challenge_id': target_challenge['id'],
            'prompt': 'generate a image like the one on screen please'
        })
        self.assertEqual(cheat_resp.status_code, 400)
        cheat_data = cheat_resp.get_json()
        self.assertTrue(cheat_data.get('is_cheating'))

        # 3. Test Valid Cloudflare Worker Generation & Dual-Image AI Evaluation (Single Shot)
        valid_prompt = "A glowing futuristic research dome surrounded by crystalline spires and volumetric golden mist, 8k"
        sample_bytes = _make_sample_jpeg_bytes()
        mock_worker_resp = MagicMock()
        mock_worker_resp.status_code = 200
        mock_worker_resp.headers = {"Content-Type": "image/jpeg"}
        mock_worker_resp.content = sample_bytes

        with patch("image_generator.requests.post", return_value=mock_worker_resp), \
             patch.object(image_generator, "_get_worker_config", return_value=("https://demo.workers.dev", "secret-key")):
            gen_resp = self.client.post('/api/generate', json={
                'participant_id': pid,
                'challenge_id': target_challenge['id'],
                'prompt': valid_prompt
            })
        self.assertEqual(gen_resp.status_code, 200)
        gen_data = gen_resp.get_json()
        self.assertTrue(gen_data['success'])
        self.assertTrue(gen_data['locked'])
        self.assertIsNotNone(gen_data.get('submission'))
        gen_rec = gen_data['generation']
        self.assertEqual(gen_rec.get('source'), 'cloudflare-workers-ai')
        self.assertIsNotNone(gen_rec.get('image_data'))

        # 3b. Enforce Single-Shot: Second generation attempt & reroll must be rejected with 403
        second_gen = self.client.post('/api/generate', json={
            'participant_id': pid,
            'challenge_id': target_challenge['id'],
            'prompt': 'A second unauthorized retry prompt'
        })
        self.assertEqual(second_gen.status_code, 403)
        self.assertTrue(second_gen.get_json().get('already_generated'))

        reroll_after = self.client.post('/api/target-challenge/new', json={'participant_id': pid})
        self.assertEqual(reroll_after.status_code, 403)
        self.assertTrue(reroll_after.get_json().get('already_generated'))

        # Check AI Judge Dual-Image Scorecard
        ev = gen_rec['evaluation']
        self.assertIn('total_score', ev)
        self.assertGreaterEqual(ev['total_score'], 0.0)
        self.assertLessEqual(ev['total_score'], 100.0)
        self.assertIn('visual_similarity', ev['breakdown'])
        self.assertIn('subject_match', ev['breakdown'])
        self.assertIn('style_match', ev['breakdown'])
        self.assertIn('prompt_precision', ev['breakdown'])
        self.assertIn('unbiased_critique', ev)

        # 4. Submit Masterpiece (idempotent — returns already auto-saved submission without duplicate)
        sub_resp = self.client.post('/api/submit', json={
            'participant_id': pid,
            'prompt': valid_prompt,
            'image_data': gen_rec['image_data']
        })
        self.assertEqual(sub_resp.status_code, 200)
        sub_data = sub_resp.get_json()
        self.assertTrue(sub_data['success'])
        self.assertEqual(sub_data['submission']['id'], gen_data['submission']['id'])
        self.assertEqual(sub_data['submission']['player_name'], 'Sarah Connor')
        self.assertEqual(sub_data['submission']['player_email'], 'sarah@resistance.edu')
        self.assertIsNotNone(sub_data['submission'].get('target_image'))

        # 5. Leaderboard Check (exact single entry for this participant)
        lb_resp = self.client.get('/api/leaderboard')
        self.assertEqual(lb_resp.status_code, 200)
        lb_data = lb_resp.get_json()
        sarah_entries = [e for e in lb_data['leaderboard'] if e['participant_id'] == pid]
        self.assertEqual(len(sarah_entries), 1)
        top = sarah_entries[0]
        self.assertEqual(top['player_name'], 'Sarah Connor')
        self.assertEqual(top['player_email'], 'sarah@resistance.edu')
        self.assertIn('target_image', top)
        self.assertIn('image_data', top)

    def test_timer_expiry_empty_prompt_locks_attempt(self):
        join_resp = self.client.post('/api/join', json={
            'name': 'Timeout Tester',
            'email': 'timeout@test.edu'
        })
        pid = join_resp.get_json()['participant']['id']

        exp_resp = self.client.post('/api/generate', json={
            'participant_id': pid,
            'prompt': '',
            'auto_triggered': True
        })
        self.assertEqual(exp_resp.status_code, 400)
        exp_data = exp_resp.get_json()
        self.assertTrue(exp_data.get('time_expired_empty'))
        self.assertTrue(exp_data.get('locked'))

        # Subsequent manual attempt after timer expiry must be blocked with 403
        retry_resp = self.client.post('/api/generate', json={
            'participant_id': pid,
            'prompt': 'Late prompt after timeout'
        })
        self.assertEqual(retry_resp.status_code, 403)
        self.assertTrue(retry_resp.get_json().get('already_generated'))

    def test_admin_authentication(self):
        admin_page_resp = self.client.get('/admin')
        self.assertEqual(admin_page_resp.status_code, 200)
        self.assertIn(b'data-admin-route="true"', admin_page_resp.data)

        home_resp = self.client.get('/')
        self.assertEqual(home_resp.status_code, 200)
        self.assertIn(b'data-admin-route="false"', home_resp.data)

        auth_resp = self.client.post('/api/admin/auth', json={'admin_code': ADMIN_CODE})
        self.assertEqual(auth_resp.status_code, 200)
        self.assertTrue(auth_resp.get_json()['success'])

    def test_competition_phase_transitions(self):
        # 1. Switch to battle phase
        battle_resp = self.client.post(
            '/api/admin/phase',
            headers={'X-Admin-Code': ADMIN_CODE},
            json={'phase': 'battle', 'duration': 180}
        )
        self.assertEqual(battle_resp.status_code, 200)
        self.assertTrue(battle_resp.get_json()['success'])
        self.assertEqual(battle_resp.get_json()['state']['status'], 'battle')

        # Verify state endpoint
        state_resp = self.client.get('/api/state')
        self.assertEqual(state_resp.status_code, 200)
        self.assertEqual(state_resp.get_json()['status'], 'battle')

        # 2. Switch to leaderboard phase
        lb_resp = self.client.post(
            '/api/admin/phase',
            headers={'X-Admin-Code': ADMIN_CODE},
            json={'phase': 'leaderboard'}
        )
        self.assertEqual(lb_resp.status_code, 200)
        self.assertEqual(lb_resp.get_json()['state']['status'], 'leaderboard')

        # 3. Switch back to lobby phase
        lobby_resp = self.client.post(
            '/api/admin/phase',
            headers={'X-Admin-Code': ADMIN_CODE},
            json={'phase': 'lobby'}
        )
        self.assertEqual(lobby_resp.status_code, 200)
        self.assertEqual(lobby_resp.get_json()['state']['status'], 'lobby')

        # 5. Reset competition
        reset_resp = self.client.post(
            '/api/admin/reset',
            headers={'X-Admin-Code': ADMIN_CODE}
        )
        self.assertEqual(reset_resp.status_code, 200)
        self.assertTrue(reset_resp.get_json()['success'])

    def test_challenge_custom_image_upload(self):
        # 1. Add challenge with base64 image
        dummy_b64 = "data:image/jpeg;base64," + base64.b64encode(b"fake_jpeg_content").decode("utf-8")
        add_resp = self.client.post(
            '/api/challenges/add',
            headers={'X-Admin-Code': ADMIN_CODE},
            json={
                'category': 'Cinematic Movie Scenes',
                'title': 'Test Upload Megacity',
                'brief': 'A test floating city challenge with uploaded image.',
                'image_data': dummy_b64
            }
        )
        self.assertEqual(add_resp.status_code, 200)
        ch_data = add_resp.get_json()['challenge']
        ch_id = ch_data['id']
        self.assertIn('static_url', ch_data)

        # 2. Upload image to existing challenge endpoint
        new_dummy_b64 = "data:image/jpeg;base64," + base64.b64encode(b"updated_jpeg_content").decode("utf-8")
        upload_resp = self.client.post(
            f'/api/challenges/{ch_id}/image',
            headers={'X-Admin-Code': ADMIN_CODE},
            json={'image_data': new_dummy_b64}
        )
        self.assertEqual(upload_resp.status_code, 200)
        self.assertTrue(upload_resp.get_json()['success'])
        self.assertIn(ch_id, upload_resp.get_json()['static_url'])

        # Clean up test file
        test_file = os.path.join("static", "images", "challenges", f"{ch_id}.jpg")
        if os.path.exists(test_file):
            try:
                os.remove(test_file)
            except Exception:
                pass
        challenge_manager.remove_challenge(ch_id)

    def test_submission_image_endpoints_and_optimization(self):
        # 1. Join and generate
        join_resp = self.client.post('/api/join', json={'name': 'Fast Loader', 'email': 'fast@load.dev'})
        pid = join_resp.get_json()['participant']['id']
        dummy_b64 = "data:image/jpeg;base64," + base64.b64encode(b"sample_generated_jpeg").decode("utf-8")
        gen_resp = self.client.post('/api/generate', json={
            'participant_id': pid,
            'prompt': 'A futuristic super-fast server room with neon fibers',
            '_test_mock_image_data': dummy_b64
        })
        self.assertEqual(gen_resp.status_code, 200)

        # 2. Check leaderboard returns lightweight URL
        lb_resp = self.client.get('/api/leaderboard')
        self.assertEqual(lb_resp.status_code, 200)
        lb_data = lb_resp.get_json()
        fast_entries = [e for e in lb_data['leaderboard'] if e['participant_id'] == pid]
        self.assertEqual(len(fast_entries), 1)
        sub_id = fast_entries[0]['id']
        self.assertTrue(fast_entries[0]['image_data'].startswith(f"/api/submission/{sub_id}/image"))

        # 3. Fetch image endpoint directly
        img_resp = self.client.get(f'/api/submission/{sub_id}/image')
        self.assertEqual(img_resp.status_code, 200)
        self.assertTrue(len(img_resp.data) > 0)
        self.assertIn("Cache-Control", img_resp.headers)


if __name__ == '__main__':
    unittest.main()
