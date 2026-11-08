from __future__ import annotations

from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Channel import GDT_Channel
from gdo.core.GDT_JSON import GDT_JSON
from gdo.language.GDT_Language import GDT_Language


class trans(Method):
    """Enable or configure a channel's automatic interpreter mode."""

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'trans'

    def gdo_in_private(self) -> bool:
        return False

    @classmethod
    def gdo_method_config_channel(cls) -> list[GDT]:
        return [
            GDT_Bool('translate_enabled').initial('0'),
            GDT_Bool('translate_paused').initial('0'),
            # A channel explicitly chooses every target language. English is
            # useful in some rooms, but must not be silently enabled.
            GDT_JSON('translate_languages').not_null().initial('[]'),
        ]

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Channel('channel'),
            GDT_Language('lang'),
            GDT_Bool('enabled').initial('1').positional(),
            GDT_Bool('pause'),
        ]

    @classmethod
    def channel_settings(cls, channel) -> tuple[bool, list[str]]:
        """Read a channel's persisted opt-in state and destination language."""
        method = cls().env_channel(channel)
        languages = method.get_config_channel_value('translate_languages')
        languages = languages if isinstance(languages, list) else []
        return (
            bool(method.get_config_channel_value('translate_enabled')) and not bool(method.get_config_channel_value('translate_paused')),
            [language for language in languages if isinstance(language, str) and len(language) == 2],
        )

    async def gdo_execute(self) -> GDT:
        # The method's own environment remains stable even when a bridge
        # creates another Message before this command is parsed.
        channel = self.param_value('channel') or self._env_channel
        raw_language = self.param_val('lang')
        language = raw_language.lower() if raw_language else None
        enabled = self.param_value('enabled')
        pause = self.param_value('pause')
        original_channel = self._env_channel
        self._env_channel = channel
        try:
            languages = self.get_config_channel_value('translate_languages')
            languages = languages if isinstance(languages, list) else []
            languages = [value.lower() for value in languages if isinstance(value, str) and len(value) == 2]
            if language:
                if enabled and language not in languages:
                    languages.append(language)
                elif not enabled:
                    languages = [value for value in languages if value != language]
                self.save_config_channel('translate_languages', GDT_JSON('languages').to_val(languages))
                self.save_config_channel('translate_enabled', '1' if languages else '0')
            if pause is not None:
                self.save_config_channel('translate_paused', '1' if pause else '0')
            paused = pause if pause is not None else bool(self.get_config_channel_value('translate_paused'))
        finally:
            self._env_channel = original_channel
        state = 'paused' if paused and languages else 'enabled' if languages else 'disabled'
        return self.reply('msg_trans_channel', (state, channel.render_name(), ', '.join(languages) or 'none'))
