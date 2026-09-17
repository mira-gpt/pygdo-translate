# pygdo-translate

An opt-in Google Translate module for the PyGDO chatbot.

No channel is translated by default. A staff member explicitly enables a
channel and selects its destination language:

```text
$trans --channel=3 --language=en
```

The module then translates ordinary channel messages through Google's public
web endpoint and posts a compact follow-up only when the detected source
language differs from the selected destination. Commands and inactive channels
are ignored.

## Example

Use `$trans --enabled=0` to disable the mode again. The integration is keyless;
Google can rate-limit or change this unofficial endpoint, in which case normal
chat continues without translation.

For a one-off translation in any channel, use an ISO-639-1 source/target pair:

```text
$en-de Hello friend
```
