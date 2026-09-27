import json
import tempfile
import unittest
from pathlib import Path

from devcontrol.semantic import build_request, assess_response


class SemanticReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'sample.txt').write_text('All four employers are present.', encoding='utf-8')
        self.contract = {'objective': 'Check saved output', 'requirements': [
            {'id': 'employers', 'statement': 'Keep all four employers.', 'evidence_paths': ['sample.txt']}]}

    def test_actual_evidence_and_explicit_options_reach_jev(self):
        body = build_request(self.contract, self.root)
        self.assertIn('All four employers', json.dumps(body['state']))
        self.assertEqual(set(body['questions']['employers']['criteria']),
                         {'SATISFIED', 'VIOLATED', 'INSUFFICIENT_EVIDENCE'})

    def test_no_credentials_or_outside_file_can_become_evidence(self):
        for path in ['.env', '../sample.txt', str(self.root / 'sample.txt')]:
            self.contract['requirements'][0]['evidence_paths'] = [path]
            with self.assertRaises(ValueError):
                build_request(self.contract, self.root)

    def test_missing_evidence_stops_before_request(self):
        self.contract['requirements'][0]['evidence_paths'] = ['missing.txt']
        with self.assertRaises(ValueError):
            build_request(self.contract, self.root)

    def test_unknown_is_not_success(self):
        body = build_request(self.contract, self.root)
        for label, expected in [('SATISFIED', True), ('VIOLATED', False), ('INSUFFICIENT_EVIDENCE', False)]:
            response = {'answers': {'employers': {'choice': label, 'confidence': 1,
                'probabilities': {k: float(k == label) for k in body['questions']['employers']['criteria']}}}}
            self.assertEqual(assess_response(response, body['questions'])['accepted'], expected)

    def test_missing_answer_cannot_pass(self):
        body = build_request(self.contract, self.root)
        with self.assertRaises(ValueError):
            assess_response({'answers': {}}, body['questions'])

    def test_large_evidence_is_rejected_not_silently_truncated(self):
        (self.root / 'sample.txt').write_text('x' * 70000)
        with self.assertRaises(ValueError):
            build_request(self.contract, self.root)


if __name__ == '__main__':
    unittest.main()
