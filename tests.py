import unittest
from app import app, ADMIN_CODE
from challenges import OFFICIAL_CATEGORIES, challenge_manager
from evaluation import ai_evaluator, validate_prompt_anti_cheat

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
        # Rule 3: Each user should have a unique image given
        t1 = challenge_manager.get_unique_target_challenge(participant_id="user-alpha-1")
        t2 = challenge_manager.get_unique_target_challenge(participant_id="user-beta-2")
        self.assertIsNotNone(t1.get("image_data"))
        self.assertIsNotNone(t2.get("image_data"))
        self.assertIn(t1["category"], OFFICIAL_CATEGORIES)
        self.assertIn(t2["category"], OFFICIAL_CATEGORIES)
        # Seeds should be different
        self.assertNotEqual(t1["seed"], t2["seed"])

    def test_end_to_end_reverse_prompt_workflow(self):
        # 1. User joins on Identifier page with Name & Email
        join_resp = self.client.post('/api/join', json={
            'name': 'Sarah Connor',
            'email': 'sarah@resistance.edu'
        })
        self.assertEqual(join_resp.status_code, 200)
        join_data = join_resp.get_json()
        self.assertTrue(join_data['success'])
        pid = join_data['participant']['id']
        target_challenge = join_data['target_challenge']

        # Ensure target image is present
        self.assertIn('image_data', target_challenge)
        self.assertTrue(len(target_challenge['image_data']) > 100)

        # Ensure hidden_prompt is NOT sent to client
        self.assertNotIn('hidden_prompt', target_challenge)

        # 2. Test Anti-Cheat Rejection via API
        cheat_resp = self.client.post('/api/generate', json={
            'participant_id': pid,
            'challenge_id': target_challenge['id'],
            'prompt': 'generate a image like the one on screen please'
        })
        self.assertEqual(cheat_resp.status_code, 400)
        cheat_data = cheat_resp.get_json()
        self.assertTrue(cheat_data.get('is_cheating'))

        # 3. Test Valid Generation & Dual-Image AI Evaluation
        valid_prompt = "A glowing futuristic research dome surrounded by crystalline spires and volumetric golden mist, 8k"
        gen_resp = self.client.post('/api/generate', json={
            'participant_id': pid,
            'challenge_id': target_challenge['id'],
            'prompt': valid_prompt
        })
        self.assertEqual(gen_resp.status_code, 200)
        gen_data = gen_resp.get_json()
        self.assertTrue(gen_data['success'])
        gen_rec = gen_data['generation']
        self.assertIsNotNone(gen_rec.get('image_data'))

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

        # 4. Submit Masterpiece & Store Score Under Name & Email
        sub_resp = self.client.post('/api/submit', json={
            'participant_id': pid,
            'prompt': valid_prompt,
            'image_data': gen_rec['image_data']
        })
        self.assertEqual(sub_resp.status_code, 200)
        sub_data = sub_resp.get_json()
        self.assertTrue(sub_data['success'])
        self.assertEqual(sub_data['submission']['player_name'], 'Sarah Connor')
        self.assertEqual(sub_data['submission']['player_email'], 'sarah@resistance.edu')
        self.assertIsNotNone(sub_data['submission'].get('target_image'))

        # 5. Leaderboard Check
        lb_resp = self.client.get('/api/leaderboard')
        self.assertEqual(lb_resp.status_code, 200)
        lb_data = lb_resp.get_json()
        self.assertGreaterEqual(len(lb_data['leaderboard']), 1)
        top = lb_data['leaderboard'][0]
        self.assertEqual(top['player_name'], 'Sarah Connor')
        self.assertEqual(top['player_email'], 'sarah@resistance.edu')
        self.assertIn('target_image', top)
        self.assertIn('image_data', top)

    def test_admin_authentication(self):
        auth_resp = self.client.post('/api/admin/auth', json={'admin_code': ADMIN_CODE})
        self.assertEqual(auth_resp.status_code, 200)
        self.assertTrue(auth_resp.get_json()['success'])

if __name__ == '__main__':
    unittest.main()
