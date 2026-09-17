from __future__ import annotations

import re

from gdo.base.GDO import GDO
from gdo.base.GDO_Module import GDO_Module
from gdo.base.Message import Message


class module_translate(GDO_Module):
    """Opt-in, channel-scoped Google Translate for PyGDO chat."""

    def gdo_classes(self) -> list[type[GDO]]:
        return []

    def gdo_subscribe_events(self):
        self.subscribe('new_message', self.on_new_message)

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
                translation = await GTranslate.translate(requested, source.lower(), target.lower())
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
        if not enabled or not targets:
            return
        for target in targets:
            try:
                translation = await GTranslate.translate(text, target=target)
            except GTranslateError:
                # Translation is an optional convenience; a remote outage must not
                # affect the original chat message or flood the channel with errors.
                continue
            if translation.source_language.lower() == target or translation.text == text:
                continue
            await channel.send(
                f'↳ {user.get_name()} [{translation.source_language}→{target}]: {translation.text}'
            )
