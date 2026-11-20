import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from gdo.translate.GTranslate import Translation
from gdo.translate.module_translate import module_translate


class AllTest(unittest.IsolatedAsyncioTestCase):
    async def test_channel_translation_uses_displayname_not_platform_id(self):
        channel = SimpleNamespace(send=AsyncMock())
        user = SimpleNamespace(get_name=lambda: '353556056934449156',
                               get_displayname=lambda: 'Tina-chan')
        message = SimpleNamespace(_env_channel=channel, _env_user=user,
                                  _message='freitags ist immer bunt gemischt',
                                  get_trigger=lambda: '$')
        with patch('gdo.translate.method.trans.trans.channel_settings', return_value=(True, ['en'])), \
                patch('gdo.translate.GTranslate.GTranslate.translate', new=AsyncMock(
                    return_value=Translation('Fridays are always a colorful mix', 'de'))), \
                patch.object(module_translate, 'cfg_google_api_key', return_value='test'):
            await module_translate().on_new_message(message)
        channel.send.assert_awaited_once_with('↳ Tina-chan [de→en]: Fridays are always a colorful mix')

    async def test_translation_completes_before_speech(self):
        channel = SimpleNamespace(get_lang_iso=lambda: 'en', send=AsyncMock())
        message = SimpleNamespace(_env_channel=channel, _env_user=object(),
                                  _message='$all Hallo Welt', get_trigger=lambda: '$',
                                  message=MagicMock())
        order = []

        async def translate(*args, **kwargs):
            order.append('translate')
            return Translation('Hello world', 'de')

        def speak(*args):
            order.append('speech')
            self.assertEqual(('audio.ipc_say', ['Hello world', 'en']), args)

        with patch('gdo.translate.method.trans.trans.channel_settings', return_value=(True, ['en'])), \
                patch('gdo.translate.GTranslate.GTranslate.translate', side_effect=translate), \
                patch.object(module_translate, 'cfg_google_api_key', return_value='test'), \
                patch('gdo.base.IPC.IPC.send_to_dog', side_effect=speak):
            await module_translate().on_new_message(message)
        self.assertEqual(['translate', 'speech'], order)
        channel.send.assert_awaited_once_with('↳ [de→en]: Hello world')
        message.message.assert_called_once_with('')

    async def test_disabled_channel_never_speaks(self):
        channel = SimpleNamespace(send=AsyncMock())
        message = SimpleNamespace(_env_channel=channel, _env_user=object(),
                                  _message='$all Hello', get_trigger=lambda: '$',
                                  message=MagicMock())
        with patch('gdo.translate.method.trans.trans.channel_settings', return_value=(False, [])), \
                patch('gdo.base.IPC.IPC.send_to_dog') as speak:
            await module_translate().on_new_message(message)
        speak.assert_not_called()
        channel.send.assert_awaited_once()
