#!/bin/bash
# speak.sh — One-command voice for CLI AI agents in WSL
# Usage: ./speak.sh "Hello world" [tone] [voice]
#
# This command WILL block for 5-10 seconds while audio plays. That is normal.
# The audio is being fetched from the API and played through Windows speakers.

TEXT="$1"
TONE="${2:-neutral}"
VOICE="${3:-paul}"
TTS_SERVER="http://localhost:8765"
TMP_WAV="/tmp/tts_output_$$.wav"

if [ -z "$TEXT" ]; then
    echo "Usage: speak.sh \"text\" [tone] [voice]"
    echo "Tones: neutral, happy, cheerful, confident, excited, sad, frustrated, angry"
    echo "Voices: paul (default), oliver, jane"
    exit 1
fi

# URL-encode the text
ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$TEXT'))" 2>/dev/null || echo "$TEXT" | sed 's/ /+/g')

# Try Voxtral TTS server first
HTTP_CODE=$(curl -s --max-time 5 -o "$TMP_WAV" -w '%{http_code}' "${TTS_SERVER}/tts?voice=${VOICE}&tone=${TONE}&text=${ENCODED}")

if [ "$HTTP_CODE" = "200" ] && [ -s "$TMP_WAV" ]; then
    # WSL: convert to Windows path and play via PowerShell
    if command -v wslpath &>/dev/null; then
        WIN_PATH=$(wslpath -w "$TMP_WAV")
        powershell.exe -Command "(New-Object Media.SoundPlayer '${WIN_PATH}').PlaySync()" 2>/dev/null
    # macOS
    elif [ "$(uname)" = "Darwin" ]; then
        afplay "$TMP_WAV"
    # Linux
    else
        aplay "$TMP_WAV" 2>/dev/null
    fi
    rm -f "$TMP_WAV"
    echo "ok"
else
    rm -f "$TMP_WAV"
    # Fallback to local system TTS
    if command -v wslpath &>/dev/null || command -v powershell.exe &>/dev/null; then
        powershell.exe -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('${TEXT//\'/\'\'}')" 2>/dev/null
    elif [ "$(uname)" = "Darwin" ]; then
        say "$TEXT"
    else
        espeak "$TEXT" 2>/dev/null
    fi
    echo "ok (local)"
fi
