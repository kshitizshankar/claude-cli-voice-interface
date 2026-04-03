# Claude CLI Voice Interface

Give Claude Code a voice. This project uses [Mistral's Voxtral TTS](https://docs.mistral.ai/capabilities/voice/) to speak Claude's responses aloud, turning your terminal into a conversational AI assistant.

Built for WSL on Windows — audio plays through Windows speakers via PowerShell.

## How it works

A lightweight Python HTTP server runs in the background. Claude Code (or any tool) sends text to it via HTTP, and you hear it spoken aloud. The server:

- **Streams sentences** — splits text into sentences, plays the first while fetching the next. You hear audio within ~2 seconds instead of waiting for the full response.
- **Rotates API keys** — manages multiple free Mistral API keys, auto-rotating on rate limits.
- **Runs persistently** — no cold starts. Start once, use all session.

## Quick start

### 1. Clone and setup

```bash
git clone https://github.com/kshitizshankar/claude-cli-voice-interface.git
cd claude-cli-voice-interface
python3 -m venv .venv
source .venv/bin/activate
pip install httpx
```

### 2. Add your Mistral API keys

Get free keys from [console.mistral.ai](https://console.mistral.ai/). Create a `keys.txt` file (one key per line):

```
your-mistral-api-key-1
your-mistral-api-key-2
# comment out bad keys with a hash
```

### 3. Start the server

```bash
source .venv/bin/activate
python3 server.py
```

The server runs on `http://localhost:8765` by default.

### 4. Test it

```bash
curl 'http://localhost:8765/speak?tone=cheerful&text=Hello+world'
```

## API

### `GET /speak`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | *(required)* | The text to speak |
| `tone` | `neutral` | Voice tone (see below) |
| `bg` | `0` | Set to `1` for fire-and-forget (returns instantly, plays in background) |

### `GET /reload`

Hot-reload `keys.txt` without restarting the server. Use this after adding or removing API keys.

### Available tones

All tones use the **Paul** (US English male) voice with different emotional expressions:

| Tone | Use for |
|------|---------|
| `neutral` | Default, questions, general speech |
| `cheerful` | Encouragement, positive feedback |
| `confident` | Key insights, strong statements |
| `excited` | Breakthroughs, great moments |
| `happy` | Positive reinforcement |
| `frustrated` | Devil's advocate, tension |
| `sad` | Empathetic moments |
| `angry` | Pressure-testing, challenging |

## Files

| File | Purpose |
|------|---------|
| `server.py` | TTS HTTP server with streaming playback and key rotation |
| `speak.py` | Standalone CLI script (uses `MISTRAL_API_KEY` env var) |
| `keys.txt` | Your Mistral API keys, one per line (gitignored) |
| `list_voices.py` | Utility to list available Voxtral voices |
| `list_all_voices.py` | Utility to list all voices with details |

## Streaming playback

For multi-sentence text, the server:

1. Splits text into sentences
2. Sends sentence 1 to the Mistral API
3. Starts playing sentence 1 audio as soon as it arrives
4. While sentence 1 plays, prefetches sentence 2 in parallel
5. Chains through all sentences seamlessly

This means you hear the first words within ~2 seconds, regardless of how long the full text is.

## Using with Claude Code

The whole point of this project is to give Claude Code a voice. Here is how to set it up.

### Step 1: Start the server

Run this before starting Claude Code (or in a separate terminal):

```bash
cd /path/to/claude-cli-voice-interface
source .venv/bin/activate
nohup python3 server.py > /tmp/tts-server.log 2>&1 &
```

### Step 2: Tell Claude how to use it

Add the prompt below to your Claude Code memory, project instructions (CLAUDE.md), or paste it at the start of a conversation.

---

## Prompt for Claude Code

> **Copy everything inside the code block into your Claude Code instructions:**

```markdown
## Voice Output

You have access to a TTS server running at http://localhost:8765. Use it to speak responses aloud.

**How to speak:**
Run this via your shell tool:
  curl -s 'http://localhost:8765/speak?tone=TONE&text=URL_ENCODED_TEXT'

For fire-and-forget (returns instantly, plays audio in background):
  curl -s 'http://localhost:8765/speak?tone=TONE&text=URL_ENCODED_TEXT&bg=1'

**Available tones:** neutral, cheerful, confident, excited, happy, frustrated, sad, angry.
Pick the tone that matches the emotional context of what you are saying.

**Rules:**
- Voice and text are DIFFERENT channels. Never duplicate content across both.
- Voice is for: short reactions, confirmations, questions, encouragement, high-level summaries.
- Text is for: code, file paths, commands, technical details, lists, anything the user needs to read or copy.
- NEVER say file paths, code, URLs, or technical details aloud. That is what text is for.
- Keep voice output SHORT — 1-2 sentences max. The server uses free API keys with rate limits.
- Think: "would a human colleague say this out loud?" If not, it is text-only.
- Use bg=1 when you do not need to wait for speech to finish before continuing your work.

**Good examples:**
- "Done, the server is updated and running."
- "Found the bug — it was a null check. Fix is in."
- "Hey, quick question — do you want me to refactor this or just patch it?"

**Bad examples (never do this):**
- "I updated slash home slash user slash server dot py with the new config."
- "The error was on line 47 of src utils parser ts where the optional chaining operator..."
- Reading out an entire paragraph of explanation that should be text.
```

---

## Running as a background service

To auto-start the server when WSL boots, add this to `~/.bashrc` or `~/.profile`:

```bash
if ! pgrep -f "python3 server.py" > /dev/null; then
    cd /path/to/claude-cli-voice-interface
    source .venv/bin/activate
    nohup python3 server.py > /tmp/tts-server.log 2>&1 &
fi
```

## Requirements

- **WSL** (Ubuntu 22.04+) on Windows
- **Python 3.10+** with `httpx`
- **Mistral API key** (free tier works)
- **PowerShell** accessible from WSL (for Windows audio playback)

## License

MIT
