"""Small async client for the official Google Cloud Translation Basic API."""

from dataclasses import dataclass
from html import unescape
from typing import Any

import httpx


class GTranslateError(RuntimeError):
    """Google Translate could not provide a usable translation."""


@dataclass(frozen=True, slots=True)
class Translation:
    text: str
    source_language: str


class GTranslate:
    """Translate text through an explicitly configured Cloud API key."""

    AUTO = 'auto'
    URL = 'https://translation.googleapis.com/language/translate/v2'

    @classmethod
    async def translate(cls, text: str, source: str = AUTO, target: str = 'en', api_key: str = '') -> Translation:
        if not text:
            return Translation('', source)
        if not api_key:
            raise GTranslateError('Google Cloud Translation API is not configured.')
        request = {'q': text, 'target': target, 'format': 'text'}
        if source != cls.AUTO:
            request['source'] = source
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(cls.URL, params={'key': api_key}, json=request)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as error:
            raise GTranslateError(f'Google Translate request failed: {error}') from error
        except ValueError as error:
            raise GTranslateError('Google Translate returned invalid JSON.') from error
        return cls.parse_response(payload, source)

    @staticmethod
    def parse_response(payload: Any, source: str = AUTO) -> Translation:
        try:
            translation = payload['data']['translations'][0]
            text = unescape(translation['translatedText'])
            source_language = translation.get('detectedSourceLanguage', source)
        except (IndexError, KeyError, TypeError) as error:
            raise GTranslateError('Google Translate returned an unknown response format.') from error
        if not text or not isinstance(source_language, str):
            raise GTranslateError('Google Translate returned no translation.')
        return Translation(text, source_language)
