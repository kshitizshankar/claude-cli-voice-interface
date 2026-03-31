# Claude CLI Voice Interface

Voice-enabled AI conversation system for Claude Code. Uses Mistral's Voxtral TTS API to speak responses aloud while you talk via voice input.

## Setup

```bash
# In WSL
cd /mnt/e/Work/Experiments/Claude-Voice-Interface
python3 -m venv .venv
source .venv/bin/activate
pip install mistralai httpx
```

## Usage

```bash
export MISTRAL_API_KEY="your-key-here"

# Basic
python3 speak.py "Hello world"

# With tone
python3 speak.py --tone confident "Let's do this"
```

## Available Tones (Paul US)

`neutral` | `happy` | `cheerful` | `confident` | `excited` | `sad` | `frustrated` | `angry`

## Requirements

- Python 3.12+
- WSL (Ubuntu) with Windows audio bridge
- Mistral API key (free tier available at console.mistral.ai)
