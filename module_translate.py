from __future__ import annotations

import re
import tomllib

from gdo.base.GDO import GDO
from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.base.Message import Message
from gdo.core.GDT_Secret import GDT_Secret


class module_translate(GDO_Module):
    """Opt-in, channel-scoped Google Cloud Translation for PyGDO chat."""

    MIN_TRANSLATABLE_BYTES = 12

    def gdo_module_config(self) -> list[GDT]:
        return [GDT_Secret('translate_google_api_key').initial(self.secret_api_key())]

    def secret_api_key(self) -> str:
        try:
            with open(self.file_path('secret.toml'), 'rb') as file:
                return str(tomllib.load(file).get('google', {}).get('api_key', ''))
        except (FileNotFoundError, tomllib.TOMLDecodeError):
            return ''

    def cfg_google_api_key(self) -> str:
        # Existing installations may already have a blank persisted config
        # value from before secret.toml was added. Prefer an explicit config,
        # but fall back to the local, ignored deployment secret.
        return self.get_config_val('translate_google_api_key') or self.secret_api_key()

    def gdo_classes(self) -> list[type[GDO]]:
        return []

    def gdo_subscribe_events(self):
        self.subscribe('new_message', self.on_new_message)

    @staticmethod
    def levenshtein_distance(left: str, right: str) -> int:
        """Return the edit distance without a third-party dependency."""
        if len(left) < len(right):
            left, right = right, left
        previous = list(range(len(right) + 1))
        for left_index, left_char in enumerate(left, 1):
            current = [left_index]
            for right_index, right_char in enumerate(right, 1):
                current.append(min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_char != right_char),
                ))
            previous = current
        return previous[-1]

    @classmethod
    def suppress_similar_translation(cls, source: str, translated: str) -> bool:
        """Suppress translations whose case-insensitive edit distance is <= 10%."""
        source = source.casefold()
        translated = translated.casefold()
        length = max(len(source), len(translated))
        return bool(length) and cls.levenshtein_distance(source, translated) * 10 <= length

    @staticmethod
    def has_minimum_readable_letters(text: str) -> bool:
        """Whether a chat line is substantial enough for language detection."""
        return (
            len(text.encode('utf-8')) >= module_translate.MIN_TRANSLATABLE_BYTES and
            sum(character.isalpha() for character in text) >= 3
        )

    @staticmethod
    def is_short_ascii_chat_word(text: str) -> bool:
        """Avoid guessing a language for IRC words such as ``wut`` or ``mkay``.

        Non-Latin short messages keep the original three-letter policy: this
        rule only targets the common, ambiguous ASCII one-word chatter.
        """
        return bool(re.fullmatch(r'[A-Za-z]{3,4}', text.strip()))

    async def on_new_message(self, message: Message):
        """Translate ordinary chat only when its channel opted in via ``$trans``."""
        channel = message._env_channel
        user = message._env_user
        text = message._message.strip()
        if not channel or not user or not text:
            return

        from .GTranslate import GTranslate, GTranslateError
        from .method.trans import trans

        # A one-off request works in every channel, e.g. ``$en-de Hello``.
        # Handle it before ordinary commands reach the parser.
        # `$de-en` is intentionally portable across connectors, including
        # channels whose ordinary command trigger is `.`.
        triggers = rf'(?:{re.escape(message.get_trigger())}|\$)'
        if one_off := re.fullmatch(rf'{triggers}([a-zA-Z]{{2}})-([a-zA-Z]{{2}})\s+(.+)', text):
            source, target, requested = one_off.groups()
            try:
                translation = await GTranslate.translate(
                    requested, source.lower(), target.lower(), self.cfg_google_api_key())
            except GTranslateError:
                await channel.send('Translation is temporarily unavailable.')
            else:
                await channel.send(f'↳ [{source.lower()}→{target.lower()}]: {translation.text}')
            # Do not let the normal command parser report ``en-de`` as unknown.
            message.message('')
            return

        if text.startswith(message.get_trigger()):
            return

        enabled, targets = trans.channel_settings(channel)
        if (not enabled or not targets or
                not self.has_minimum_readable_letters(text) or
                self.is_short_ascii_chat_word(text)):
            return
        for target in targets:
            try:
                translation = await GTranslate.translate(text, target=target, api_key=self.cfg_google_api_key())
            except GTranslateError:
                # Translation is an optional convenience; a remote outage must not
                # affect the original chat message or flood the channel with errors.
                continue
            if (translation.source_language.lower() == target or
                    self.suppress_similar_translation(text, translation.text)):
                continue
            await channel.send(
                f'↳ {user.get_name()} [{translation.source_language}→{target}]: {translation.text}'
            )
