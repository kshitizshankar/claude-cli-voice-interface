#!/usr/bin/env python3
"""Voxtral TTS script for Claude Code voice interface."""
import sys
import os
import base64
import subprocess
import tempfile

PAUL_VOICES = {
    "neutral":    "c69964a6-ab8b-4f8a-9465-ec0925096ec8",
    "happy":      "1024d823-a11e-43ee-bf3d-d440dccc0577",
    "cheerful":   "01d985cd-5e0c-4457-bfd8-80ba31a5bc03",
    "confident":  "98559b22-62b5-4a64-a7cd-fc78ca41faa8",
    "excited":    "5940190b-f58a-4c3e-8264-a40d63fd6883",
    "sad":        "530e2e20-58e2-45d8-b0a5-4594f4915944",
    "frustrated": "1f017bcb-02e5-460d-989b-db065c0c6122",
    "angry":      "cb891218-482c-4392-9878-91e8d999d57a",
}

def speak(text: str, tone: str = "neutral"):
    import httpx

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("Error: MISTRAL_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    voice_id = PAUL_VOICES.get(tone, PAUL_VOICES["neutral"])

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
        subprocess.run(["aplay", tmp_path], check=True, capture_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        try:
            win_path = subprocess.run(
                ["wslpath", "-w", tmp_path],
                capture_output=True, text=True
            ).stdout.strip()
            subprocess.run(
                ["powershell.exe", "-Command",
                 f"(New-Object Media.SoundPlayer '{win_path}').PlaySync()"],
                check=True, capture_output=True
            )
        except Exception as e:
            print(f"Could not play audio: {e}", file=sys.stderr)
            print(f"Audio saved to: {tmp_path}")
            return

    os.unlink(tmp_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: speak.py [--tone neutral|happy|cheerful|confident|excited|sad|frustrated|angry] <text>")
        sys.exit(1)

    tone = "neutral"
    args = sys.argv[1:]
    if args[0] == "--tone" and len(args) > 2:
        tone = args[1]
        args = args[2:]

    speak(" ".join(args), tone=tone)
