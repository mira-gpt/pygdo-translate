import unittest
import re

from gdo.translate.GTranslate import GTranslate, Translation


class TranslateTest(unittest.TestCase):
    def test_parse_google_response(self):
        payload = [[['Hello', '안녕하세요', None, None]], None, 'ko']
        self.assertEqual(Translation('Hello', 'ko'), GTranslate.parse_response(payload))

    def test_invalid_google_response_is_rejected(self):
        with self.assertRaises(Exception):
            GTranslate.parse_response([])

    def test_one_off_command_pattern(self):
        match = re.fullmatch(r'\$([a-zA-Z]{2})-([a-zA-Z]{2})\s+(.+)', '$en-de Hello friend')
        self.assertEqual(('en', 'de', 'Hello friend'), match.groups())
