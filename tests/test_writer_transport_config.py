import tempfile
import unittest
from pathlib import Path

from harness.provider import OpenRouter
from harness.store import RunStore


class WriterTransportConfigTests(unittest.TestCase):
    def test_reasoning_writer_has_room_to_return_json(self):
        def transport(endpoint, body, key):
            # Reproduce the observed empty response when reasoning uses the cap.
            content = '{"ready": true}' if body['max_tokens'] > 5000 else ''
            self.assertEqual(body.get('reasoning'), {'effort': 'low'})
            return {'choices': [{'message': {'content': content}}]}

        with tempfile.TemporaryDirectory() as folder:
            provider = OpenRouter(RunStore(Path(folder)), {
                'writer_model': 'deepseek/deepseek-v4-pro-0813',
                'writer_max_tokens': 32000, 'writer_reasoning_effort': 'low',
            }, 'test-key', transport)
            self.assertEqual(provider.create('Return JSON', {}), {'ready': True})

    def test_legacy_configuration_keeps_original_request_defaults(self):
        def transport(endpoint, body, key):
            self.assertEqual(body['max_tokens'], 5000)
            self.assertNotIn('reasoning', body)
            return {'choices': [{'message': {'content': '{}'}}]}

        with tempfile.TemporaryDirectory() as folder:
            provider = OpenRouter(RunStore(Path(folder)), {
                'writer_model': 'legacy-writer',
            }, 'test-key', transport)
            self.assertEqual(provider.create('Return JSON', {}), {})
