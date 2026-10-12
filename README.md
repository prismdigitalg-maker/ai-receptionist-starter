# AI Receptionist — build your own, own your data

A working AI phone/browser receptionist built on **[OpenRouter](https://openrouter.ai)**.
One API key does all three jobs:

| Job | What it is | Model (edit in `config.yaml`) |
|---|---|---|
| **Ears** | speech → text | `openai/gpt-4o-mini-transcribe` |
| **Brain** | decides what to say | `google/gemini-2.5-flash-lite` |
| **Voice** | text → speech | `elevenlabs/eleven-flash-v2.5` |

No subscriptions. No per-seat fees. You pay **pennies per call** and you own the whole thing.

## Quick start

```bash
# 1. get a key at https://openrouter.ai/keys  (add a few $ of credit)
export OPENROUTER_API_KEY=sk-or-...        # Windows PowerShell: setx OPENROUTER_API_KEY "sk-or-..."

# 2. run it (Python 3.11+ and ffmpeg required — see the course, Module 2)
python server.py

# 3. open the page and talk to it
#    http://localhost:8765   →  Answer call  →  Tap to talk  →  speak  →  tap again
```

There are **no Python dependencies** — it is standard library only.

## Make it yours

Open `config.yaml` and change the business, the assistant's name, the opening hours, the
services, the models and the voice. Save, restart, done. **That is the entire "customisation"
for a new client — the same code serves a dentist, a law firm, a gym or a plumber.**

## How it works

```
caller speaks ─▶ OpenRouter STT ─▶ OpenRouter LLM ─▶ OpenRouter TTS ─▶ caller hears
                 (ears)             (brain)            (voice)
```

`server.py` receives audio, transcribes it, asks the model, speaks the answer and returns
the audio to the page. Swap the browser mic for a phone number (Twilio/Telnyx) and it
answers real calls — that is Module 11 of the course.

## Files

```
server.py        the whole backend (stdlib only)
config.yaml      the business + models + voice  ← edit this
static/index.html  the call UI
static/caller.mp3  a sample caller clip (for demos/tests)
```

## Licence

MIT — use it, rebrand it, sell it.
