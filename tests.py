import unittest
from app import app, ADMIN_CODE
from challenges import OFFICIAL_CATEGORIES, challenge_manager
from evaluation import ai_evaluator

class TestFullWorkflow(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_end_to_end_battle_flow(self):
        # 1. Join with Name and Email
        join_resp = self.client.post('/api/join', json={
            'name': 'Aria Stark',
            'email': 'aria@winterfell.edu'
        })
        self.assertEqual(join_resp.status_code, 200)
        join_data = join_resp.get_json()
        pid = join_data['participant']['id']
        self.assertEqual(join_data['participant']['name'], 'Aria Stark')
        self.assertEqual(join_data['participant']['email'], 'aria@winterfell.edu')
        challenge = join_data['challenge']
        self.assertIn('title', challenge)
        self.assertIn('category', challenge)

        # 2. Re-roll challenge test
        reroll_resp = self.client.post('/api/reroll-challenge', json={
            'participant_id': pid
        })
        self.assertEqual(reroll_resp.status_code, 200)
        reroll_data = reroll_resp.get_json()
        self.assertTrue(reroll_data['success'])
        self.assertIn('challenge', reroll_data)

        # 3. Direct submit test
        prompt = 'Autonomous biophilic learning pods surrounded by bioluminescent trees and quantum diagrams, cinematic 8k'
        sub_resp = self.client.post('/api/submit', json={
            'participant_id': pid,
            'prompt': prompt,
            'image_data': 'data:image/jpeg;base64,fakeimagebytes123'
        })
        self.assertEqual(sub_resp.status_code, 200)
        sub_data = sub_resp.get_json()
        self.assertTrue(sub_data['success'])
        sub_id = sub_data['submission']['id']
        ai_score = sub_data['submission']['ai_score']
        self.assertEqual(sub_data['submission']['player_name'], 'Aria Stark')
        self.assertEqual(sub_data['submission']['player_email'], 'aria@winterfell.edu')

        # 4. Community Vote
        vote_resp = self.client.post('/api/vote', json={
            'submission_id': sub_id,
            'voter_id': 'other_voter_999'
        })
        self.assertEqual(vote_resp.status_code, 200)
        vote_data = vote_resp.get_json()
        self.assertEqual(vote_data['votes'], 1)
        self.assertEqual(vote_data['total_score'], round(ai_score + 2.0, 1))

        # 5. Leaderboard Check (stores score under name and email)
        lb_resp = self.client.get('/api/leaderboard')
        self.assertEqual(lb_resp.status_code, 200)
        lb_data = lb_resp.get_json()
        self.assertGreaterEqual(len(lb_data['leaderboard']), 1)
        first = lb_data['leaderboard'][0]
        self.assertEqual(first['player_name'], 'Aria Stark')
        self.assertEqual(first['player_email'], 'aria@winterfell.edu')

    def test_consistent_evaluation_across_all_categories(self):
        # Test evaluation calibration on all 8 categories
        for cat in OFFICIAL_CATEGORIES:
            ch = challenge_manager.get_active_challenges(category=cat)[0]
            title = ch['title']
            test_prompt = f"Visionary forward-thinking design for {title}, cinematic volumetric light, 8k render"
            ev = ai_evaluator.evaluate_submission(test_prompt, ch, 'TestPlayer')
            self.assertGreaterEqual(ev['total_score'], 40.0)
            self.assertLessEqual(ev['total_score'], 100.0)
            self.assertIn('thematic_relevance', ev['breakdown'])
            self.assertIn('creativity_originality', ev['breakdown'])
            self.assertIn('prompt_engineering', ev['breakdown'])
            self.assertIn('future_impact', ev['breakdown'])

    def test_admin_and_challenge_management(self):
        # 1. Auth check
        auth_resp = self.client.post('/api/admin/auth', json={'admin_code': ADMIN_CODE})
        self.assertEqual(auth_resp.status_code, 200)
        self.assertTrue(auth_resp.get_json()['success'])

        # 2. Add challenge
        new_ch_resp = self.client.post('/api/challenges/add', json={
            'category': 'Future of Education',
            'title': 'Test Neural Library',
            'brief': 'A test neural library in the clouds',
            'visual_goals': 'Volumetric clouds and glowing crystals',
            'inspiration_keywords': 'Hologram, Quantum Books',
            'evaluation_focus': 'Education and AI',
            'is_active': True
        }, headers={'X-Admin-Code': ADMIN_CODE})
        self.assertEqual(new_ch_resp.status_code, 200)
        new_ch = new_ch_resp.get_json()['challenge']
        ch_id = new_ch['id']

        # 3. Toggle challenge active status
        toggle_resp = self.client.post(f'/api/challenges/{ch_id}/toggle', json={'is_active': False}, headers={'X-Admin-Code': ADMIN_CODE})
        self.assertEqual(toggle_resp.status_code, 200)

        # 4. Delete challenge
        del_resp = self.client.delete(f'/api/challenges/{ch_id}', headers={'X-Admin-Code': ADMIN_CODE})
        self.assertEqual(del_resp.status_code, 200)

if __name__ == '__main__':
    unittest.main()
