# Claude CLI Voice Interface

Give Claude Code a voice. Uses [Mistral's Voxtral TTS](https://docs.mistral.ai/capabilities/voice/) to speak Claude's responses aloud — turning your terminal into a conversational AI assistant.

Runs anywhere: Docker, macOS, Linux, Windows, WSL.

## Quick start

### Docker (recommended)

```bash
git clone https://github.com/kshitizshankar/claude-cli-voice-interface.git
cd claude-cli-voice-interface

# Add your keys
cp .env.example .env
# Edit .env with your Mistral API key(s)

# Build and run
docker build -t claude-voice .
docker run -d -p 8765:8765 --env-file .env --name claude-voice claude-voice
```

With Docker, use `/tts` (returns audio bytes) — your client handles playback since the container can't access speakers.

```bash
# Test it
curl -o test.wav 'http://localhost:8765/tts?tone=cheerful&text=Hello+world'
# Play with your OS audio player
```

### Native Python

```bash
git clone https://github.com/kshitizshankar/claude-cli-voice-interface.git
cd claude-cli-voice-interface
python3 -m venv .venv
source .venv/bin/activate
pip install httpx

cp .env.example .env
# Edit .env with your Mistral API key(s)

python3 server.py
```

```bash
# Test — server plays audio directly
curl 'http://localhost:8765/speak?tone=cheerful&text=Hello+world'
```

### Get your API keys

Free keys from [console.mistral.ai](https://console.mistral.ai/). Add them to `.env`:

```bash
MISTRAL_API_KEYS=key1,key2,key3
```

Multiple keys enable automatic rotation when one hits rate limits.

## API

### `GET /speak` — server plays audio

Best for native (non-Docker) setups where the server can access your speakers.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | *(required)* | The text to speak |
| `tone` | `neutral` | Voice tone (see below) |
| `bg` | `0` | Set to `1` for fire-and-forget (returns instantly, plays in background) |

For multi-sentence text, uses streaming playback — plays each sentence as it arrives while prefetching the next in parallel.

### `GET /tts` — returns WAV audio bytes

Best for Docker, remote deployments, or when the client handles playback.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | *(required)* | The text to speak |
| `tone` | `neutral` | Voice tone (see below) |

Returns `audio/wav` content. Zero temp files created server-side.

### `GET /reload`

Hot-reload `.env` without restarting the server. Use after adding or rotating API keys.

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

## Streaming playback

For multi-sentence text (via `/speak`), the server:

1. Splits text into sentences
2. Fetches audio for sentence 1 from the Mistral API
3. Starts playing sentence 1 as soon as it arrives (~2 seconds)
4. While sentence 1 plays, prefetches sentence 2 in parallel
5. Chains through all sentences seamlessly

You hear the first words within ~2 seconds, regardless of total text length.

## Using with Claude Code

### Step 1: Start the server

**Docker:**
```bash
docker run -d -p 8765:8765 --env-file .env --restart unless-stopped --name claude-voice claude-voice
```

**Native:**
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
- Voice is for: reactions, confirmations, questions, encouragement, high-level summaries.
  For discussions and back-and-forth, longer conversational voice is great.
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

## Auto-start

**Docker** — use `--restart unless-stopped` (shown above).

**Native** — add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
if ! pgrep -f "python3 server.py" > /dev/null; then
    cd /path/to/claude-cli-voice-interface
    source .venv/bin/activate
    nohup python3 server.py > /tmp/tts-server.log 2>&1 &
fi
```

## Files

| File | Purpose |
|------|---------|
| `server.py` | TTS HTTP server with streaming playback and key rotation |
| `Dockerfile` | Container image — Python 3.12-slim + httpx |
| `.env.example` | Template for API keys |
| `speak.py` | Standalone CLI script |
| `list_voices.py` | List available Voxtral voices |
| `list_all_voices.py` | List all voices with details |

## Requirements

- **Python 3.10+** with `httpx` — or just **Docker**
- **Mistral API key** — free tier works ([console.mistral.ai](https://console.mistral.ai/))
- For `/speak` (server-side playback): auto-detects `afplay` (macOS), `aplay` (Linux), PowerShell (Windows/WSL)

## License

MIT
