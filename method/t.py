from __future__ import annotations

from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_RestOfText import GDT_RestOfText
from gdo.language.GDT_Language import GDT_Language

from ..GTranslate import GTranslate, GTranslateError
from ..module_translate import module_translate


class t(Method):
    """Translate one text using automatic source-language detection."""

    @classmethod
    def gdo_trigger(cls) -> str:
        return 't'

    def gdo_in_private(self) -> bool:
        return False

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Language('lang').not_null().initial('en'),
            GDT_RestOfText('text').not_null(),
        ]

    async def gdo_execute(self) -> GDT:
        target = self.param_val('lang')
        text = self.param_value('text')
        try:
            translation = await GTranslate.translate(
                text, target=target, api_key=module_translate.instance().cfg_google_api_key())
        except GTranslateError:
            return self.reply('err_trans_unavailable')
        return self.reply('msg_trans_text', (
            translation.source_language.lower(), target, translation.text,
        ))
