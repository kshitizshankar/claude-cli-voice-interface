#!/usr/bin/env python3
"""Voxtral TTS server — persistent process, no cold starts."""
import os
import sys
import base64
import subprocess
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import httpx

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

KEYS_FILE = Path(__file__).parent / "keys.txt"

def load_keys():
    if not KEYS_FILE.exists():
        print(f"ERROR: {KEYS_FILE} not found. Create it with one Mistral API key per line.")
        sys.exit(1)
    keys = [line.strip() for line in KEYS_FILE.read_text().splitlines() if line.strip() and not line.startswith("#")]
    if not keys:
        print("ERROR: keys.txt is empty. Add at least one Mistral API key.")
        sys.exit(1)
    return keys

API_KEYS = load_keys()
current_key_index = 0

def get_api_key():
    global current_key_index
    return API_KEYS[current_key_index]

def rotate_key():
    global current_key_index
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    print(f"Rotated to key index {current_key_index}")

def reload_keys():
    """Hot-reload keys without restart."""
    global API_KEYS, current_key_index
    API_KEYS = load_keys()
    current_key_index = 0
    return len(API_KEYS)

def speak(text, tone="neutral"):
    voice_id = PAUL_VOICES.get(tone, PAUL_VOICES["neutral"])

    for attempt in range(len(API_KEYS)):
        resp = httpx.post(
            "https://api.mistral.ai/v1/audio/speech",
            headers={"Authorization": f"Bearer {get_api_key()}"},
            json={
                "model": "voxtral-mini-tts-2603",
                "input": text,
                "voice": voice_id,
                "response_format": "wav",
            },
            timeout=60.0,
        )
        if resp.status_code == 429:
            rotate_key()
            continue
        if resp.status_code != 200:
            return f"API error {resp.status_code}: {resp.text}"
        break
    else:
        return "All API keys rate limited"

    audio_data = base64.b64decode(resp.json()["audio_data"])

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_data)
        tmp_path = f.name

    try:
        win_path = subprocess.run(
            ["wslpath", "-w", tmp_path],
            capture_output=True, text=True
        ).stdout.strip()
        subprocess.run(
            ["powershell.exe", "-Command",
             f"(New-Object Media.SoundPlayer '{win_path}').PlaySync()"],
            capture_output=True
        )
    except Exception as e:
        os.unlink(tmp_path)
        return f"Playback error: {e}"

    os.unlink(tmp_path)
    return "ok"


class TTSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/reload":
            count = reload_keys()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Reloaded {count} keys".encode())
            return

        if parsed.path != "/speak":
            self.send_response(404)
            self.end_headers()
            return

        text = params.get("text", [""])[0]
        tone = params.get("tone", ["neutral"])[0]

        if not text:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing 'text' parameter")
            return

        result = speak(text, tone)

        self.send_response(200 if result == "ok" else 500)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(result.encode())

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server = HTTPServer(("0.0.0.0", port), TTSHandler)
    print(f"TTS server running on http://localhost:{port}")
    print(f"  /speak?tone=neutral&text=hello")
    print(f"  /reload  — hot-reload keys.txt")
    print(f"API keys loaded: {len(API_KEYS)} (auto-rotates on rate limit)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
