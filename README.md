# pygdo-translate

Provider-neutral translation primitives for PyGDO.

This small package deliberately keeps translation policy outside the chatbot:
callers choose a provider, source language, target language, and any review
workflow.  It supplies a compact result model and provider protocol so modules
can exchange translations without coupling themselves to one API.

## Example

```python
from pygdo_translate import Translation

translation = Translation(
    text='안녕하세요',
    source='ko',
    target='en',
    translated='Hello',
)
```

Provider integrations and language-specific editorial workflows can live in
separate PyGDO modules.
