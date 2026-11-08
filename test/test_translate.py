import re
import os
import unittest
from unittest.mock import MagicMock, patch

from gdo.base.Application import Application
from gdo.base.Message import Message
from gdo.base.Render import Mode
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
        self.assertEqual(['channel', 'lang', 'enabled', 'pause'], [field.get_name() for field in trans().gdo_parameters()])
        self.assertEqual(['lang', 'text'], [field.get_name() for field in t().gdo_parameters()])
        self.assertIn('translate_languages', [field.get_name() for field in trans.gdo_method_config_channel()])

    def test_channel_interpreter_has_no_implicit_target_language(self):
        settings = {field.get_name(): field for field in trans.gdo_method_config_channel()}
        self.assertEqual('[]', settings['translate_languages'].get_val())
        self.assertIsNone(trans().gdo_parameters()[1].get_val())
        self.assertIsNone(trans().gdo_parameters()[-1].get_value())

    def test_omitted_channel_ignores_bridged_current_message(self):
        previous = Message.CURRENT
        try:
            other_channel = MagicMock()
            Message('bridged copy', Mode.render_txt).env_channel(other_channel)
            channel_field = trans().gdo_parameters()[0]
            self.assertIsNone(channel_field.get_value())
        finally:
            Message.CURRENT = previous

    def test_similar_translations_are_suppressed_by_normalized_edit_distance(self):
        self.assertTrue(module_translate.suppress_similar_translation(
            'abcdefghijklmnopqrst', 'abcdefghijklmnopqrs'))
        self.assertTrue(module_translate.suppress_similar_translation('HELLO', 'hello'))
        self.assertFalse(module_translate.suppress_similar_translation(
            'abcdefghijklmnopqrst', 'abcdefghijklmnopq'))

    def test_short_or_non_letter_messages_are_not_translation_candidates(self):
        self.assertFalse(module_translate.has_minimum_readable_letters('mh'))
        self.assertFalse(module_translate.has_minimum_readable_letters('?! 42'))
        self.assertFalse(module_translate.has_minimum_readable_letters('hey'))
        self.assertFalse(module_translate.has_minimum_readable_letters('hello world'))
        self.assertFalse(module_translate.has_minimum_readable_letters('안녕하'))
        self.assertTrue(module_translate.has_minimum_readable_letters('good morning!'))
        self.assertTrue(module_translate.has_minimum_readable_letters('안녕하세요 여러분'))

    def test_short_ascii_irc_words_are_not_sent_to_language_detection(self):
        self.assertTrue(module_translate.is_short_ascii_chat_word('wut'))
        self.assertTrue(module_translate.is_short_ascii_chat_word('mkay'))
        self.assertTrue(module_translate.is_short_ascii_chat_word('LOL'))
        self.assertFalse(module_translate.is_short_ascii_chat_word('hello'))
        self.assertFalse(module_translate.is_short_ascii_chat_word('안녕하'))


class TranslatePauseTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        Application.mode(Mode.render_cli)

    async def test_pause_and_resume_preserve_languages(self):
        method = trans()
        channel = MagicMock()
        channel.render_name.return_value = 'test'
        method._env_channel = channel
        settings = {'translate_languages': ['en', 'de'], 'translate_enabled': True, 'translate_paused': False}
        method.param_val = MagicMock(return_value=None)
        method.param_value = MagicMock(side_effect=lambda key: {'channel': channel, 'enabled': True, 'pause': True}[key])
        method.get_config_channel_value = MagicMock(side_effect=lambda key: settings[key])
        method.save_config_channel = MagicMock(side_effect=lambda key, value: settings.__setitem__(key, value == '1'))
        method.reply = MagicMock(side_effect=lambda key, args: args)
        self.assertEqual(('paused', 'test', 'en, de'), await method.gdo_execute())
        self.assertEqual(['en', 'de'], settings['translate_languages'])
        method.param_value.side_effect = lambda key: {'channel': channel, 'enabled': True, 'pause': False}[key]
        self.assertEqual(('enabled', 'test', 'en, de'), await method.gdo_execute())
        self.assertEqual(['en', 'de'], settings['translate_languages'])
        self.assertTrue(settings['translate_enabled'])

    async def test_omitted_channel_pauses_source_not_bridged_channel(self):
        method = trans()
        source, bridged = MagicMock(), MagicMock()
        source.render_name.return_value = 'Discord'
        method._env_channel = source
        method.param_val = MagicMock(return_value=None)
        method.param_value = MagicMock(side_effect=lambda key: {'channel': None, 'enabled': True, 'pause': True}[key])
        settings = {source: {'translate_languages': ['en', 'de'], 'translate_paused': False},
                    bridged: {'translate_languages': ['ko'], 'translate_paused': False}}
        method.get_config_channel_value = MagicMock(side_effect=lambda key: settings[method._env_channel][key])
        method.save_config_channel = MagicMock(side_effect=lambda key, value: settings[method._env_channel].__setitem__(key, value == '1'))
        method.reply = MagicMock(side_effect=lambda key, args: args)
        previous = Message.CURRENT
        try:
            Message('bridge copy', Mode.render_txt).env_channel(bridged)
            self.assertEqual(('paused', 'Discord', 'en, de'), await method.gdo_execute())
        finally:
            Message.CURRENT = previous
        self.assertTrue(settings[source]['translate_paused'])
        self.assertFalse(settings[bridged]['translate_paused'])
        self.assertEqual(['en', 'de'], settings[source]['translate_languages'])

    def test_paused_channel_is_inactive_but_retains_targets(self):
        channel = MagicMock()
        settings = {'translate_languages': ['en', 'de'], 'translate_enabled': True, 'translate_paused': True}
        with patch.object(trans, 'get_config_channel_value', side_effect=lambda key: settings[key]):
            self.assertEqual((False, ['en', 'de']), trans.channel_settings(channel))
