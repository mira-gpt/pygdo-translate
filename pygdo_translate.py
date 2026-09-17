"""Provider-neutral translation types for PyGDO modules."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Translation:
    """A translated text together with its language metadata."""

    text: str
    source: str
    target: str
    translated: str


class Translator(Protocol):
    """Interface implemented by asynchronous translation providers."""

    async def translate(self, text: str, source: str = 'auto', target: str = 'en') -> Translation:
        """Translate *text* from *source* to *target*."""
