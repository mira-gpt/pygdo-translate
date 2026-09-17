"""Small async client for Google Translate's public web endpoint."""

from dataclasses import dataclass
from typing import Any

import httpx


class GTranslateError(RuntimeError):
    """Google Translate could not provide a usable translation."""


@dataclass(frozen=True, slots=True)
class Translation:
    text: str
    source_language: str


class GTranslate:
    """Translate text without storing it or requiring a project API key."""

    AUTO = 'auto'
    URL = 'https://translate.googleapis.com/translate_a/single'

    @classmethod
    async def translate(cls, text: str, source: str = AUTO, target: str = 'en') -> Translation:
        if not text:
            return Translation('', source)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(cls.URL, data={
                    'client': 'gtx', 'sl': source, 'tl': target, 'dt': 't', 'q': text,
                }, headers={'User-Agent': 'PyGDO-Translate/0.1'})
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as error:
            raise GTranslateError(f'Google Translate request failed: {error}') from error
        except ValueError as error:
            raise GTranslateError('Google Translate returned invalid JSON.') from error
        return cls.parse_response(payload)

    @staticmethod
    def parse_response(payload: Any) -> Translation:
        try:
            text = ''.join(segment[0] for segment in payload[0] if segment and segment[0])
            source_language = payload[2]
        except (IndexError, KeyError, TypeError) as error:
            raise GTranslateError('Google Translate returned an unknown response format.') from error
        if not text or not isinstance(source_language, str):
            raise GTranslateError('Google Translate returned no translation.')
        return Translation(text, source_language)
