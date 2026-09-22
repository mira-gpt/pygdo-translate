import re
import os
import unittest

from gdo.base.Application import Application
from gdo.translate.GTranslate import GTranslate, Translation
from gdo.translate.method.t import t
from gdo.translate.method.trans import trans
from gdo.translate.module_translate import module_translate


class TranslateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Application.init(os.path.dirname(__file__) + '/../../../')
        Application.init_cli()

    def test_parse_google_response(self):
        payload = {'data': {'translations': [{'translatedText': 'Hello', 'detectedSourceLanguage': 'ko'}]}}
        self.assertEqual(Translation('Hello', 'ko'), GTranslate.parse_response(payload))

    def test_parse_google_response_keeps_explicit_source(self):
        payload = {'data': {'translations': [{'translatedText': 'Hallo'}]}}
        self.assertEqual(Translation('Hallo', 'en'), GTranslate.parse_response(payload, 'en'))

    def test_invalid_google_response_is_rejected(self):
        with self.assertRaises(Exception):
            GTranslate.parse_response([])

    def test_one_off_command_pattern(self):
        match = re.fullmatch(r'\$([a-zA-Z]{2})-([a-zA-Z]{2})\s+(.+)', '$en-de Hello friend')
        self.assertEqual(('en', 'de', 'Hello friend'), match.groups())

    def test_one_off_pattern_accepts_all_iso_pairs(self):
        match = re.fullmatch(r'\$([a-zA-Z]{2})-([a-zA-Z]{2})\s+(.+)', '$ko-en 안녕하세요')
        self.assertEqual(('ko', 'en', '안녕하세요'), match.groups())

    def test_short_chat_triggers(self):
        self.assertEqual('trans', trans.gdo_trigger())
        self.assertEqual('t', t.gdo_trigger())
        self.assertEqual(['channel', 'lang', 'enabled'], [field.get_name() for field in trans().gdo_parameters()])
        self.assertEqual(['lang', 'text'], [field.get_name() for field in t().gdo_parameters()])
        self.assertIn('translate_languages', [field.get_name() for field in trans.gdo_method_config_channel()])

    def test_channel_interpreter_has_no_implicit_target_language(self):
        settings = {field.get_name(): field for field in trans.gdo_method_config_channel()}
        self.assertEqual('[]', settings['translate_languages'].get_val())
        self.assertIsNone(trans().gdo_parameters()[1].get_val())

    def test_similar_translations_are_suppressed_by_normalized_edit_distance(self):
        self.assertTrue(module_translate.suppress_similar_translation(
            'abcdefghijklmnopqrst', 'abcdefghijklmnopqrs'))
        self.assertTrue(module_translate.suppress_similar_translation('HELLO', 'hello'))
        self.assertFalse(module_translate.suppress_similar_translation(
            'abcdefghijklmnopqrst', 'abcdefghijklmnopq'))

    def test_short_or_non_letter_messages_are_not_translation_candidates(self):
        self.assertFalse(module_translate.has_minimum_readable_letters('mh'))
        self.assertFalse(module_translate.has_minimum_readable_letters('?! 42'))
        self.assertTrue(module_translate.has_minimum_readable_letters('hey'))
        self.assertTrue(module_translate.has_minimum_readable_letters('안녕하'))
