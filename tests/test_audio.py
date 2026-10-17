"""Anonymous media boundaries and metadata removal, without network access."""
import unittest
from unittest.mock import Mock
from engine.audio import AudioError, AudioStore, allowed_preview, strip_mp3_metadata


class AudioTests(unittest.TestCase):
    def test_only_preview_host_and_https_are_allowed(self):
        self.assertTrue(allowed_preview('https://p.scdn.co/mp3-preview/abc'))
        for value in [None, '', 'http://p.scdn.co/x', 'https://p.scdn.co.evil.test/x',
                      'https://u:p@p.scdn.co/x', 'https://p.scdn.co:bad/x',
                      'https://p.scdn.co:80/x', 'https://[invalid/x', 'file:///etc/passwd']:
            with self.subTest(value=value):
                self.assertFalse(allowed_preview(value))

    def test_strips_both_id3_tags_without_touching_audio(self):
        frames = b'\xff\xfb' + b'frames' * 100
        title = b'TIT2 artist and title'
        header = b'ID3\x03\x00\x00\x00\x00\x00' + bytes([len(title)])
        self.assertEqual(strip_mp3_metadata(header + title + frames + b'TAG' + b'x' * 125), frames)
        self.assertEqual(strip_mp3_metadata(frames), frames)

    def test_absent_source_and_invalid_preview_are_safe_errors(self):
        store = AudioStore()
        for track in [{'track_id': None}, {'preview_url': 'https://localhost/private'}]:
            with self.assertRaises(AudioError):
                store.get(track)

    def test_download_strips_metadata_and_uses_bounded_cache(self):
        store = AudioStore(capacity=1)
        response = Mock()
        response.geturl.return_value = 'https://p.scdn.co/a'
        response.headers = {'Content-Type': 'audio/mpeg'}
        response.read.return_value = b'\xff\xfb' + b'audio' * 20
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        store.opener.open = Mock(return_value=response)
        self.assertEqual(store.get({'preview_url': 'https://p.scdn.co/a'}), response.read.return_value)
        store.get({'preview_url': 'https://p.scdn.co/a'})
        self.assertEqual(store.opener.open.call_count, 1)
        response.geturl.return_value = 'https://p.scdn.co/b'
        store.get({'preview_url': 'https://p.scdn.co/b'})
        self.assertEqual(list(store.cache), ['https://p.scdn.co/b'])
