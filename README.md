# CLI AI Agents' Voice Interface

Give your AI coding agent a voice. Uses [Mistral's Voxtral TTS](https://docs.mistral.ai/capabilities/voice/) to speak responses aloud — turning your terminal into a conversational AI assistant.

Works with **any CLI agent** that can run shell commands: Claude Code, Cursor, Copilot CLI, Aider, Gemini CLI, or even plain curl. Runs anywhere: Docker, macOS, Linux, Windows, WSL.

Includes a zero-dependency local TTS fallback that needs no API key at all.

## Two ways to get voice

### 1. Voxtral TTS (high quality, needs API key)

Natural-sounding voice with emotional tones via Mistral's free API. Requires a [free API key](https://console.mistral.ai/).

### 2. Local system TTS (instant, zero setup)

Every major OS has built-in text-to-speech. No server, no API key, no dependencies. Sounds robotic but works instantly:

```bash
# macOS
say "Hello world"

# Windows / WSL
powershell.exe -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('Hello world')"

# Linux (install espeak if not present)
espeak "Hello world"
```

**You can use both** — Voxtral for quality, local TTS as a fallback when the server is down or you don't want to burn API credits.

## Quick start (Voxtral)

### Docker (recommended)

```bash
git clone https://github.com/kshitizshankar/cli-agents-voice-interface.git
cd cli-agents-voice-interface

# Add your keys
cp .env.example .env
# Edit .env with your Mistral API key(s)

# Build and run
docker build -t cli-voice .
docker run -d -p 8765:8765 --env-file .env --name cli-voice cli-voice
```

With Docker, use `/tts` (returns audio bytes) — your client handles playback since the container can't access speakers.

```bash
# Test — fetch WAV and play locally
curl -o test.wav 'http://localhost:8765/tts?tone=cheerful&text=Hello+world'
afplay test.wav        # macOS
aplay test.wav         # Linux
# Windows: powershell.exe -Command "(New-Object Media.SoundPlayer 'test.wav').PlaySync()"
```

### Native Python

```bash
git clone https://github.com/kshitizshankar/cli-agents-voice-interface.git
cd cli-agents-voice-interface
python3 -m venv .venv
source .venv/bin/activate
pip install httpx

cp .env.example .env
# Edit .env with your Mistral API key(s)

python3 server.py
```

```bash
# Test — server plays audio directly through your speakers
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
| `voice` | `paul` | Voice character: `paul`, `oliver`, or `jane` |
| `tone` | `neutral` | Emotional tone (see below) |
| `bg` | `0` | Set to `1` for fire-and-forget (returns instantly, plays in background) |

For multi-sentence text, uses streaming playback — plays each sentence as it arrives while prefetching the next in parallel.

### `GET /tts` — returns WAV audio bytes

Best for Docker, remote deployments, or when the client handles playback.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | *(required)* | The text to speak |
| `voice` | `paul` | Voice character: `paul`, `oliver`, or `jane` |
| `tone` | `neutral` | Emotional tone (see below) |

Returns `audio/wav` content. Zero temp files created server-side.

### `GET /voices` — list available voices

Returns JSON with all voice characters and their available tones.

### `GET /reload`

Hot-reload `.env` without restarting the server. Use after adding or rotating API keys.

### Voice characters

| Voice | Gender | Accent | Available tones |
|-------|--------|--------|-----------------|
| `paul` (default) | Male | US English | neutral, happy, cheerful, confident, excited, sad, frustrated, angry |
| `oliver` | Male | British English | neutral |
| `jane` | Female | British English | sarcasm |

If you request a tone that doesn't exist for a voice (e.g. `oliver` + `excited`), it gracefully falls back to that voice's default tone.

**Want a different voice?** Mistral's Voxtral TTS supports voice cloning from a few seconds of audio — any accent, any language. See the [Voxtral TTS docs](https://docs.mistral.ai/capabilities/voice/) for details. You can also browse all preset voices with the included `list_voices.py` script.

### Multi-agent setup

Give each AI agent a distinct voice so you can tell them apart:

```
Claude Code  → voice=paul    (US male, 8 emotional tones)
Gemini CLI   → voice=oliver  (British male)
Third agent  → voice=jane    (British female, sarcastic)
```

## Streaming playback

For multi-sentence text (via `/speak`), the server:

1. Splits text into sentences
2. Fetches audio for sentence 1 from the Mistral API
3. Starts playing sentence 1 as soon as it arrives (~2 seconds)
4. While sentence 1 plays, prefetches sentence 2 in parallel
5. Chains through all sentences seamlessly

You hear the first words within ~2 seconds, regardless of total text length.

## Using with your AI agent

This works with any CLI AI agent that can execute shell commands — Claude Code, Cursor, Copilot CLI, Aider, Gemini CLI, etc.

### Step 1: Start the server (optional — local TTS needs no server)

**Docker:**
```bash
docker run -d -p 8765:8765 --env-file .env --restart unless-stopped --name cli-voice cli-voice
```

**Native:**
```bash
cd /path/to/cli-agents-voice-interface
source .venv/bin/activate
nohup python3 server.py > /tmp/tts-server.log 2>&1 &
```

### Step 2: Add the voice prompt to your agent

Add the prompt below to your agent's instructions — CLAUDE.md for Claude Code, system prompt for Gemini CLI, custom instructions for Cursor, etc.

---

## Voice Prompt for AI Agents

> **Copy everything inside the code block into your agent's instructions.**
> Replace `/path/to/speak.sh` with the actual path where you cloned the repo.

```markdown
## Voice Output

You can speak responses aloud using a helper script. The script handles everything:
Voxtral TTS if the server is running, automatic fallback to local system TTS if not,
and cross-platform audio playback (macOS, Linux, Windows, WSL).

### How to speak

Run this command to speak:
  /path/to/speak.sh "Your text here" TONE VOICE

Examples:
  /path/to/speak.sh "Hello! Let me take a look at this code." cheerful paul
  /path/to/speak.sh "Interesting approach here." confident oliver
  /path/to/speak.sh "Oh wonderful, another singleton pattern." sarcasm jane

Parameters:
  - Text (required): what to say
  - Tone (optional, default: neutral): neutral, happy, cheerful, confident, excited, sad, frustrated, angry
  - Voice (optional, default: paul): paul (US male), oliver (British male), jane (British female)

IMPORTANT: This command blocks for 5-10 seconds while audio plays through the speakers.
That is normal — it is fetching audio from an API and playing it. Do not cancel it.
If the TTS server is not running, it automatically falls back to local system TTS (faster, robotic).

### How it works (so you understand the architecture)

In WSL, you are running Linux but audio hardware belongs to Windows. Linux audio tools
like aplay cannot reach Windows speakers. The script handles this by:
1. Fetching a WAV file from the TTS server (Docker or native)
2. Converting the Linux file path to a Windows path using wslpath
3. Playing audio via powershell.exe which runs on the Windows side and can access speakers
4. Cleaning up the temp file

On macOS it uses afplay, on native Linux it uses aplay. The script auto-detects.

### Rules
- Voice and text are DIFFERENT channels. Never duplicate content across both.
- Voice is for: reactions, confirmations, questions, encouragement, high-level summaries.
  For discussions and back-and-forth, longer conversational voice is great.
- Text is for: code, file paths, commands, technical details, lists, anything to read or copy.
- NEVER say file paths, code, URLs, or technical details aloud. That is what text is for.
- Think: "would a human colleague say this out loud?" If not, it is text-only.

### Good examples
- "Done, the server is updated and running."
- "Found the bug — it was a null check. Fix is in."
- "Hey, quick question — do you want me to refactor this or just patch it?"

### Bad examples (never do this)
- "I updated slash home slash user slash server dot py with the new config."
- "The error was on line 47 of src utils parser ts where the optional chaining..."
- Reading out file paths, URLs, or code aloud.
```

---

## Auto-start

**Docker** — use `--restart unless-stopped` (shown above).

**Native** — add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
if ! pgrep -f "python3 server.py" > /dev/null; then
    cd /path/to/cli-agents-voice-interface
    source .venv/bin/activate
    nohup python3 server.py > /tmp/tts-server.log 2>&1 &
fi
```

## Files

| File | Purpose |
|------|---------|
| `server.py` | TTS HTTP server with streaming playback, voice selection, and key rotation |
| `speak.sh` | One-command voice for agents — handles platform detection, playback, and fallback |
| `Dockerfile` | Container image — Python 3.12-slim + httpx |
| `.env.example` | Template for API keys |
| `speak.py` | Standalone Python CLI script |
| `LICENSE` | MIT license |
| `list_voices.py` | List available Voxtral voices |
| `list_all_voices.py` | List all voices with details |

## Requirements

**For Voxtral TTS:**
- **Python 3.10+** with `httpx` — or just **Docker**
- **Mistral API key** — free tier works ([console.mistral.ai](https://console.mistral.ai/))
- For `/speak` (server-side playback): auto-detects `afplay` (macOS), `aplay` (Linux), PowerShell (Windows/WSL)

**For local system TTS:**
- Nothing. Built into macOS, Windows, and most Linux distros.

## License

MIT
