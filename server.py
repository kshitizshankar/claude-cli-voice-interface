#!/usr/bin/env python3
"""Voxtral TTS server — persistent process with streaming playback.

Two modes:
  /speak  — fetches audio AND plays it server-side (local use)
  /tts    — returns WAV bytes over HTTP, no temp files (Docker / remote use)
"""
import os
import sys
import re
import base64
import subprocess
import tempfile
import threading
import platform
import shutil
import glob
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import httpx

# ── Voice presets ──
# Each voice character maps tones to Mistral voice IDs.
# Default is "paul". Pass ?voice=oliver or ?voice=jane to switch.

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

DEFAULT_VOICE = "paul"

def resolve_voice_id(voice_name, tone):
    """Resolve a voice name + tone to a Mistral voice ID."""
    voice_name = voice_name.lower()
    voice = VOICES.get(voice_name, VOICES[DEFAULT_VOICE])
    # Try the requested tone, fall back to first available tone for this voice
    if tone in voice:
        return voice[tone]
    # Fall back: first available tone for this voice character
    return next(iter(voice.values()))

ENV_FILE = Path(__file__).parent / ".env"

def _parse_env_file(path):
    """Parse a .env file into a dict."""
    env = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env

def load_keys():
    """Load API keys from .env file (MISTRAL_API_KEYS=key1,key2) or env var."""
    env = _parse_env_file(ENV_FILE)
    raw = env.get("MISTRAL_API_KEYS") or os.environ.get("MISTRAL_API_KEYS")

    if not raw:
        raw = env.get("MISTRAL_API_KEY") or os.environ.get("MISTRAL_API_KEY")
        if not raw:
            print("ERROR: No API keys found.")
            print("  Set MISTRAL_API_KEYS=key1,key2 in .env or as an environment variable.")
            sys.exit(1)
        return [raw]

    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys:
        print("ERROR: MISTRAL_API_KEYS is empty.")
        sys.exit(1)
    return keys

API_KEYS = load_keys()
current_key_index = 0
key_lock = threading.Lock()

def get_api_key():
    with key_lock:
        return API_KEYS[current_key_index]

def rotate_key():
    global current_key_index
    with key_lock:
        current_key_index = (current_key_index + 1) % len(API_KEYS)
        print(f"Rotated to key index {current_key_index}")

def reload_keys():
    global API_KEYS, current_key_index
    with key_lock:
        API_KEYS = load_keys()
        current_key_index = 0
    return len(API_KEYS)

# ── Platform detection ──

def _detect_platform():
    """Detect audio playback method: wsl, macos, linux, or windows."""
    if shutil.which("wslpath"):
        return "wsl"
    system = platform.system()
    if system == "Darwin":
        return "macos"
    elif system == "Linux":
        return "linux"
    elif system == "Windows":
        return "windows"
    return "linux"

PLATFORM = _detect_platform()

# ── Sentence splitting ──

def split_sentences(text):
    """Split text into speakable chunks. Keeps it natural."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    merged = []
    for part in parts:
        if merged and len(merged[-1]) < 20:
            merged[-1] = merged[-1] + " " + part
        else:
            merged.append(part)
    if len(merged) <= 1 or len(text) < 80:
        return [text]
    return merged

# ── TTS API call ──

def fetch_audio(text, voice_id):
    """Call Mistral API and return wav bytes, or error string."""
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

    return base64.b64decode(resp.json()["audio_data"])

# ── Audio playback (cross-platform) with guaranteed cleanup ──

def play_wav(wav_bytes):
    """Write wav to temp file, play it, always clean up."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", prefix="tts_", delete=False) as f:
            f.write(wav_bytes)
            tmp_path = f.name

        if PLATFORM == "wsl":
            win_path = subprocess.run(
                ["wslpath", "-w", tmp_path],
                capture_output=True, text=True
            ).stdout.strip()
            subprocess.run(
                ["powershell.exe", "-Command",
                 f"(New-Object Media.SoundPlayer '{win_path}').PlaySync()"],
                capture_output=True, timeout=120
            )
        elif PLATFORM == "macos":
            subprocess.run(["afplay", tmp_path], check=True, capture_output=True, timeout=120)
        elif PLATFORM == "windows":
            subprocess.run(
                ["powershell.exe", "-Command",
                 f"(New-Object Media.SoundPlayer '{tmp_path}').PlaySync()"],
                capture_output=True, timeout=120
            )
        else:  # linux
            subprocess.run(["aplay", tmp_path], check=True, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        return "Playback timed out"
    except Exception as e:
        return f"Playback error: {e}"
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    return "ok"

# ── Periodic cleanup of any orphaned temp files ──

def cleanup_stale_wavs():
    """Delete any tts_*.wav files older than 5 minutes. Runs periodically."""
    while True:
        time.sleep(300)
        try:
            pattern = os.path.join(tempfile.gettempdir(), "tts_*.wav")
            cutoff = time.time() - 300
            for path in glob.glob(pattern):
                if os.path.getmtime(path) < cutoff:
                    os.unlink(path)
                    print(f"Cleaned up stale temp file: {path}")
        except Exception:
            pass

# ── Main speak functions ──

def speak_simple(text, tone="neutral", voice="paul"):
    """Blocking speak — single API call."""
    voice_id = resolve_voice_id(voice, tone)
    result = fetch_audio(text, voice_id)
    if isinstance(result, str):
        return result
    return play_wav(result)

def speak_streaming(text, tone="neutral", voice="paul"):
    """Streaming speak — split into sentences, prefetch next while playing current."""
    voice_id = resolve_voice_id(voice, tone)
    sentences = split_sentences(text)

    if len(sentences) == 1:
        return speak_simple(text, tone, voice)

    print(f"Streaming {len(sentences)} chunks ({voice}/{tone}): {[s[:30] for s in sentences]}")

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(fetch_audio, sentences[0], voice_id)]

        for i, sentence in enumerate(sentences):
            audio = futures[i].result()
            if isinstance(audio, str):
                return audio

            if i + 1 < len(sentences):
                futures.append(pool.submit(fetch_audio, sentences[i + 1], voice_id))

            result = play_wav(audio)
            if result != "ok":
                return result

    return "ok"

# ── Background playback for fire-and-forget ──

bg_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tts-bg")

def speak_background(text, tone="neutral", voice="paul"):
    """Fire and forget — returns immediately, plays in background."""
    bg_executor.submit(speak_streaming, text, tone, voice)
    return "ok"

# ── HTTP server ──

class TTSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # ── /reload ──
        if parsed.path == "/reload":
            count = reload_keys()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Reloaded {count} keys".encode())
            return

        # ── /voices — list available voices ──
        if parsed.path == "/voices":
            import json
            info = {}
            for name, tones in VOICES.items():
                info[name] = list(tones.keys())
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(info, indent=2).encode())
            return

        # ── /tts — return audio bytes, no server-side playback ──
        if parsed.path == "/tts":
            text = params.get("text", [""])[0]
            tone = params.get("tone", ["neutral"])[0]
            voice = params.get("voice", [DEFAULT_VOICE])[0]
            if not text:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing 'text' parameter")
                return

            voice_id = resolve_voice_id(voice, tone)
            result = fetch_audio(text, voice_id)

            if isinstance(result, str):
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(result.encode())
            else:
                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", str(len(result)))
                self.end_headers()
                self.wfile.write(result)
            return

        # ── /speak — fetch + play server-side ──
        if parsed.path == "/speak":
            text = params.get("text", [""])[0]
            tone = params.get("tone", ["neutral"])[0]
            voice = params.get("voice", [DEFAULT_VOICE])[0]
            bg = params.get("bg", ["0"])[0]

            if not text:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing 'text' parameter")
                return

            if bg == "1":
                result = speak_background(text, tone, voice)
            else:
                result = speak_streaming(text, tone, voice)

            self.send_response(200 if result == "ok" else 500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(result.encode())
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server = HTTPServer(("0.0.0.0", port), TTSHandler)

    cleanup_thread = threading.Thread(target=cleanup_stale_wavs, daemon=True)
    cleanup_thread.start()

    print(f"TTS server running on http://localhost:{port}")
    print(f"  Platform: {PLATFORM}")
    print(f"  Voices: {', '.join(VOICES.keys())} (default: {DEFAULT_VOICE})")
    print(f"  /speak?voice=paul&tone=neutral&text=hello")
    print(f"  /speak?voice=oliver&text=hello&bg=1")
    print(f"  /tts?voice=jane&tone=sarcasm&text=hello")
    print(f"  /voices                                (list voices)")
    print(f"  /reload                                (hot-reload keys)")
    print(f"API keys loaded: {len(API_KEYS)} (auto-rotates on rate limit)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
