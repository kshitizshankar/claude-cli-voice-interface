#!/usr/bin/env python3
"""Standalone Voxtral TTS script — speak text from the command line.

Usage:
  MISTRAL_API_KEY=your-key python3 speak.py "Hello world"
  MISTRAL_API_KEY=your-key python3 speak.py --voice oliver --tone neutral "Hello world"
"""
import sys
import os
import base64
import subprocess
import tempfile
import shutil

VOICES = {
    "paul": {
        "neutral":    "c69964a6-ab8b-4f8a-9465-ec0925096ec8",
        "happy":      "1024d823-a11e-43ee-bf3d-d440dccc0577",
        "cheerful":   "01d985cd-5e0c-4457-bfd8-80ba31a5bc03",
        "confident":  "98559b22-62b5-4a64-a7cd-fc78ca41faa8",
        "excited":    "5940190b-f58a-4c3e-8264-a40d63fd6883",
        "sad":        "530e2e20-58e2-45d8-b0a5-4594f4915944",
        "frustrated": "1f017bcb-02e5-460d-989b-db065c0c6122",
        "angry":      "cb891218-482c-4392-9878-91e8d999d57a",
    },
    "oliver": {
        "neutral":    "e3596645-b1af-469e-b857-f18ddedc7652",
    },
    "jane": {
        "sarcasm":    "a3e41ea8-020b-44c0-8d8b-f6cc03524e31",
    },
}

def resolve_voice_id(voice_name, tone):
    voice = VOICES.get(voice_name.lower(), VOICES["paul"])
    if tone in voice:
        return voice[tone]
    return next(iter(voice.values()))

def speak(text: str, tone: str = "neutral", voice: str = "paul"):
    import httpx

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("Error: MISTRAL_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    voice_id = resolve_voice_id(voice, tone)

    resp = httpx.post(
        "https://api.mistral.ai/v1/audio/speech",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "voxtral-mini-tts-2603",
            "input": text,
            "voice": voice_id,
            "response_format": "wav",
        },
        timeout=60.0,
    )
    if resp.status_code != 200:
        print(f"API error {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)
    audio_data = base64.b64decode(resp.json()["audio_data"])

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_data)
        tmp_path = f.name

    try:
        if shutil.which("wslpath"):
            # WSL: play via Windows PowerShell
            win_path = subprocess.run(
                ["wslpath", "-w", tmp_path],
                capture_output=True, text=True
            ).stdout.strip()
            subprocess.run(
                ["powershell.exe", "-Command",
                 f"(New-Object Media.SoundPlayer '{win_path}').PlaySync()"],
                check=True, capture_output=True
            )
        elif sys.platform == "darwin":
            subprocess.run(["afplay", tmp_path], check=True, capture_output=True)
        else:
            subprocess.run(["aplay", tmp_path], check=True, capture_output=True)
    except Exception as e:
        print(f"Could not play audio: {e}", file=sys.stderr)
        print(f"Audio saved to: {tmp_path}")
        return

    os.unlink(tmp_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: speak.py [--voice paul|oliver|jane] [--tone TONE] <text>")
        print("Voices: paul (US male), oliver (British male), jane (British female)")
        print("Tones:  neutral, happy, cheerful, confident, excited, sad, frustrated, angry")
        sys.exit(1)

    tone = "neutral"
    voice = "paul"
    args = sys.argv[1:]

    while len(args) > 1:
        if args[0] == "--tone":
            tone = args[1]
            args = args[2:]
        elif args[0] == "--voice":
            voice = args[1]
            args = args[2:]
        else:
            break

    speak(" ".join(args), tone=tone, voice=voice)
