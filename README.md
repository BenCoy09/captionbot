# CaptionBot

Say (or type) what you're selling. Get a WhatsApp status caption you can post.

Built for the DEV Hacktoberfest Weekend Challenge: Build for a Friend, for small clothing sellers in Nigeria who post stock on WhatsApp every day.

## How it works

- Gemma (open-weight, `gemma3:1b`) runs locally through [Ollama](https://ollama.com). No paid API.
- Speak into the page (Chrome voice typing) or type. The text box is editable, so fix any mishears before you tap **Write caption**.
- The server cleans common voice mishears ("12 key" to "12k"), then asks Gemma for ONE caption.
- A check rejects captions that drop the price or sizes, or invent a price that was never given. It retries up to 3 times.
- **Copy** or **Send to WhatsApp** (opens WhatsApp with the text ready).

Single Python file, standard library only.

## Run it

1. Install [Ollama](https://ollama.com) and [Python](https://www.python.org/downloads/).
2. `ollama pull gemma3:1b`
3. `python captionbot.py`
4. Open http://localhost:8000 in **Chrome**.

Use another model: `set MODEL=gemma3:4b` (Windows) then run the script.

## Honest limits

- Chrome's voice typing uses Google's servers, so only the model part is fully local.
- Voice typing mishears numbers and struggles with Nigerian Pidgin. Typed Pidgin works better.
- Small models copy their prompt examples. An early version of this prompt leaked a "40k" price from an example into a caption with no price. Fixed by changing the examples, adding a rule, and checking in code.
- Always read the caption before posting.

## Next

- Better Nigerian-accent speech recognition (a local Whisper model)
- Compare `gemma3:1b` with `gemma3:4b`
- Let a seller paste her own past listings as style examples

Tested by the author, not yet by a seller.
