# Claude CLI Voice Interface

Give Claude Code a voice. This project uses [Mistral's Voxtral TTS](https://docs.mistral.ai/capabilities/voice/) to speak Claude's responses aloud, turning your terminal into a conversational AI assistant.

Runs anywhere — native Python, Docker, WSL, macOS, Linux. Audio playback auto-detects your platform.

## How it works

A lightweight Python HTTP server runs in the background. Claude Code (or any tool) sends text to it via HTTP, and you hear it spoken aloud. The server:

- **Streams sentences** — splits text into sentences, plays the first while fetching the next. You hear audio within ~2 seconds instead of waiting for the full response.
- **Rotates API keys** — manages multiple free Mistral API keys, auto-rotating on rate limits.
- **Runs persistently** — no cold starts. Start once, use all session.
- **Two modes** — `/speak` plays audio server-side, `/tts` returns WAV bytes for client-side playback (Docker-friendly).

## Quick start

### Option A: Native Python

```bash
git clone https://github.com/kshitizshankar/claude-cli-voice-interface.git
cd claude-cli-voice-interface
python3 -m venv .venv
source .venv/bin/activate
pip install httpx
```

Create `keys.txt` with your Mistral API keys (one per line):

```
your-mistral-api-key-1
your-mistral-api-key-2
# comment out bad keys with a hash
```

Start the server:

```bash
python3 server.py
```

### Option B: Docker

```bash
docker build -t claude-voice .
docker run -d -p 8765:8765 -v /path/to/keys.txt:/app/keys.txt claude-voice
```

With Docker, use the `/tts` endpoint (returns audio bytes) since the container can't access your speakers. Your client (Claude Code, browser, etc.) handles playback.

### Test it

```bash
# Server-side playback (native only)
curl 'http://localhost:8765/speak?tone=cheerful&text=Hello+world'

# Get WAV bytes back (works with Docker too)
curl -o test.wav 'http://localhost:8765/tts?tone=cheerful&text=Hello+world'
```

## API

### `GET /speak` — server plays audio

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | *(required)* | The text to speak |
| `tone` | `neutral` | Voice tone (see below) |
| `bg` | `0` | Set to `1` for fire-and-forget (returns instantly, plays in background) |

For multi-sentence text, streams playback — plays each sentence as it arrives while prefetching the next.

### `GET /tts` — returns WAV audio bytes

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | *(required)* | The text to speak |
| `tone` | `neutral` | Voice tone (see below) |

Returns `audio/wav` content. No temp files created server-side. Ideal for Docker or remote deployments where the client handles playback.

### `GET /reload`

Hot-reload `keys.txt` without restarting the server.

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
| `Dockerfile` | Container image — just Python + httpx |
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

**Native:**
```bash
cd /path/to/claude-cli-voice-interface
source .venv/bin/activate
nohup python3 server.py > /tmp/tts-server.log 2>&1 &
```

**Docker:**
```bash
docker run -d -p 8765:8765 -v /path/to/keys.txt:/app/keys.txt claude-voice
```

### Step 2: Tell Claude how to use it

Add the prompt below to your Claude Code memory, project instructions (CLAUDE.md), or paste it at the start of a conversation.

---

## Prompt for Claude Code

> **Copy everything inside the code block into your Claude Code instructions:**

```markdown
## Voice Output

You have access to a TTS server running at http://localhost:8765. Use it to speak responses aloud.

**How to speak (server-side playback):**
  curl -s 'http://localhost:8765/speak?tone=TONE&text=URL_ENCODED_TEXT'

**Fire-and-forget (returns instantly, plays in background):**
  curl -s 'http://localhost:8765/speak?tone=TONE&text=URL_ENCODED_TEXT&bg=1'

**Client-side playback (for Docker or remote server):**
  curl -s -o /tmp/tts.wav 'http://localhost:8765/tts?tone=TONE&text=URL_ENCODED_TEXT'
  Then play /tmp/tts.wav with the platform audio command (afplay on Mac, aplay on Linux,
  powershell SoundPlayer on Windows) and delete the file after.

**Available tones:** neutral, cheerful, confident, excited, happy, frustrated, sad, angry.
Pick the tone that matches the emotional context of what you are saying.

**Rules:**
- Voice and text are DIFFERENT channels. Never duplicate content across both.
- Voice is for: short reactions, confirmations, questions, encouragement, high-level summaries.
  For discussions and back-and-forth, longer conversational voice is fine.
- Text is for: code, file paths, commands, technical details, lists, anything to read or copy.
- NEVER say file paths, code, URLs, or technical details aloud. That is what text is for.
- Think: "would a human colleague say this out loud?" If not, it is text-only.
- Use bg=1 when you do not need to wait for speech to finish before continuing.

**Good examples:**
- "Done, the server is updated and running."
- "Found the bug — it was a null check. Fix is in."
- "Hey, quick question — do you want me to refactor this or just patch it?"

**Bad examples (never do this):**
- "I updated slash home slash user slash server dot py with the new config."
- "The error was on line 47 of src utils parser ts where the optional chaining operator..."
- Reading out file paths, URLs, or code aloud.
```

---

## Running as a background service

To auto-start the server, add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
if ! pgrep -f "python3 server.py" > /dev/null; then
    cd /path/to/claude-cli-voice-interface
    source .venv/bin/activate
    nohup python3 server.py > /tmp/tts-server.log 2>&1 &
fi
```

Or use Docker with `--restart unless-stopped`:

```bash
docker run -d --restart unless-stopped -p 8765:8765 -v /path/to/keys.txt:/app/keys.txt claude-voice
```

## Requirements

- **Python 3.10+** with `httpx` (or Docker)
- **Mistral API key** — free tier works ([console.mistral.ai](https://console.mistral.ai/))
- **Audio playback** (for `/speak` only) — auto-detects: `afplay` (macOS), `aplay` (Linux), PowerShell SoundPlayer (Windows/WSL)

## License

MIT
