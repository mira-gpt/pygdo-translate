from __future__ import annotations

from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Channel import GDT_Channel
from gdo.language.GDT_Language import GDT_Language


class trans(Method):
    """Enable or configure a channel's automatic Google Translate mode."""

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'trans'

    def gdo_in_private(self) -> bool:
        return False

    @classmethod
    def gdo_method_config_channel(cls) -> list[GDT]:
        return [
            GDT_Bool('translate_enabled').initial('0'),
            GDT_Language('translate_language').not_null().initial('en'),
        ]

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Channel('channel').default_current(),
            GDT_Language('language').not_null().initial('en'),
            GDT_Bool('enabled').initial('1'),
        ]

    @classmethod
    def channel_settings(cls, channel) -> tuple[bool, str]:
        """Read a channel's persisted opt-in state and destination language."""
        method = cls().env_channel(channel)
        return (
            bool(method.get_config_channel_value('translate_enabled')),
            method.get_config_channel_val('translate_language'),
        )

    async def gdo_execute(self) -> GDT:
        channel = self.param_value('channel')
        language = self.param_val('language')
        enabled = self.param_value('enabled')
        original_channel = self._env_channel
        self._env_channel = channel
        try:
            self.save_config_channel('translate_enabled', '1' if enabled else '0')
            self.save_config_channel('translate_language', language)
        finally:
            self._env_channel = original_channel
        state = 'enabled' if enabled else 'disabled'
        return self.reply('msg_trans_channel', (state, channel.render_name(), language))
