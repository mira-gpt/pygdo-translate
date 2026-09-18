# pygdo-translate

An opt-in Google Cloud Translation module for the PyGDO chatbot.

## Google Cloud setup

Create a Google Cloud project, enable **Cloud Translation API**, enable billing,
then create an API key restricted to that API. Copy `secret.example.toml` to
`secret.toml` and put the key there before installing or reinstalling the
module. The module uses the official Cloud Translation Basic v2 endpoint;
without a key, translation is deliberately unavailable rather than falling
back to the unstable public web endpoint.

No channel is translated by default. A staff member explicitly enables a
channel and selects its destination language:

```text
$trans --lang=en 1
```

The module then translates ordinary channel messages through the official
Google Cloud API and posts a compact follow-up only when the detected source
language differs from the selected destination. Commands and inactive channels
are ignored.

## Example

Running `$trans --lang=ko 1` adds Korean as a second destination; each normal
message is then translated to both English and Korean. Use `$trans --lang=en 0`
to remove only English (and likewise for any other target). Normal chat
continues unchanged if the translation provider is unavailable.

For a one-off translation in any channel, use an ISO-639-1 source/target pair:

```text
$en-de Hello friend
```

Every valid ISO-639-1 source/target pair is accepted, for example `$ko-en 안녕하세요`.

To translate one text with automatic source-language detection, use:

```text
$t --lang=en Hallo friend
```
