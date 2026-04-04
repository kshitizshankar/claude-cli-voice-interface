#!/usr/bin/env python3
"""AI vs AI Rapid-Fire Quiz — CLI AI Agents' Voice Interface Demo.

Two AI agents (Paul & Oliver) compete in a quiz hosted by Jane.
Showcases multiple voices, emotional tones, and the voice interface.

Usage: python3 quiz.py
Requires TTS server at localhost:8765
"""
import time
import random
import urllib.parse
import subprocess
import shutil
import sys
import os

TTS_SERVER = "http://localhost:8765"

# ── Platform detection ──

def detect_platform():
    if shutil.which("wslpath"):
        return "wsl"
    if sys.platform == "darwin":
        return "mac"
    if sys.platform == "win32":
        return "windows"
    return "linux"

PLATFORM = detect_platform()

def speak(text, tone="neutral", voice="paul", pause=0.4):
    """Speak text via TTS server, fall back to local TTS."""
    encoded = urllib.parse.quote(text)
    tmp = f"/tmp/quiz_tts_{os.getpid()}.wav"

    result = subprocess.run(
        ["curl", "-s", "--max-time", "10", "-o", tmp, "-w", "%{http_code}",
         f"{TTS_SERVER}/tts?voice={voice}&tone={tone}&text={encoded}"],
        capture_output=True, text=True
    )

    if result.stdout.strip() == "200" and os.path.exists(tmp) and os.path.getsize(tmp) > 0:
        try:
            if PLATFORM == "wsl":
                win_path = subprocess.run(
                    ["wslpath", "-w", tmp], capture_output=True, text=True
                ).stdout.strip()
                subprocess.run(
                    ["powershell.exe", "-Command",
                     f"(New-Object Media.SoundPlayer '{win_path}').PlaySync()"],
                    capture_output=True
                )
            elif PLATFORM == "mac":
                subprocess.run(["afplay", tmp], capture_output=True)
            elif PLATFORM == "windows":
                subprocess.run(
                    ["powershell.exe", "-Command",
                     f"(New-Object Media.SoundPlayer '{tmp}').PlaySync()"],
                    capture_output=True
                )
            else:
                subprocess.run(["aplay", tmp], capture_output=True)
        except Exception:
            pass
    else:
        # Fallback
        if PLATFORM in ("wsl", "windows"):
            safe = text.replace("'", "''")
            subprocess.run(
                ["powershell.exe", "-Command",
                 f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{safe}')"],
                capture_output=True
            )
        elif PLATFORM == "mac":
            subprocess.run(["say", text], capture_output=True)
        else:
            subprocess.run(["espeak", text], capture_output=True)

    try:
        os.unlink(tmp)
    except OSError:
        pass

    time.sleep(pause)


# ── Quiz data ──
# Each question has the answer, a wrong answer, and who wins (randomized)

ROUNDS = [
    {
        "q": "What does HTML stand for?",
        "answer": "Hypertext Markup Language",
        "wrong": "High Tech Modern Language",
        "paul_wins": True,
        "paul_speed": "fast",
    },
    {
        "q": "What HTTP status code means Not Found?",
        "answer": "404",
        "wrong": "500",
        "paul_wins": False,
        "paul_speed": "slow",
    },
    {
        "q": "What Python keyword creates a function?",
        "answer": "def",
        "wrong": "func",
        "paul_wins": True,
        "paul_speed": "fast",
    },
    {
        "q": "What port does HTTPS use?",
        "answer": "443",
        "wrong": "8080",
        "paul_wins": False,
        "paul_speed": "slow",
    },
    {
        "q": "What does API stand for?",
        "answer": "Application Programming Interface",
        "wrong": "Automated Program Integration",
        "paul_wins": True,
        "paul_speed": "medium",
    },
    {
        "q": "Who created Git?",
        "answer": "Linus Torvalds",
        "wrong": "Bill Gates",
        "paul_wins": True,
        "paul_speed": "fast",
    },
    {
        "q": "What does CSS stand for?",
        "answer": "Cascading Style Sheets",
        "wrong": "Computer Styling System",
        "paul_wins": False,
        "paul_speed": "slow",
    },
    {
        "q": "In Python, what is the output of bool(0)?",
        "answer": "False",
        "wrong": "True",
        "paul_wins": True,
        "paul_speed": "fast",
    },
]

# ── Reaction pools ──

JANE_CORRECT = [
    "Correct. How thrilling.",
    "Right answer. Try not to let it go to your head.",
    "Well done. I suppose even a broken clock is right twice a day.",
    "Correct. The bar was low but you cleared it.",
]

JANE_WRONG = [
    "Wrong. Spectacularly wrong.",
    "Oh dear. That was painful to witness.",
    "Incorrect. I felt that one in my soul.",
    "Wrong. And you said it with such confidence too.",
]

JANE_BOTH_RIGHT = [
    "Both correct. How boring.",
    "You both got it. Where is the drama?",
]

PAUL_REACTIONS = {
    "win": [
        "Yes! Got it!",
        "Boom. Nailed it.",
        "Too easy.",
    ],
    "lose": [
        "Ah, I knew that one too.",
        "Alright, fair play Oliver.",
        "Next one is mine.",
    ],
}

OLIVER_REACTIONS = {
    "win": [
        "Rather straightforward, really.",
        "Elementary.",
        "I do believe that's a point for me.",
    ],
    "lose": [
        "Well played, Paul.",
        "Hmm, I was a fraction too slow.",
        "Right then. Next question.",
    ],
}


def print_banner(text, char="═"):
    width = 60
    print(f"\n{char * width}")
    print(f"  {text}")
    print(f"{char * width}")


def print_score(paul_score, oliver_score, total):
    print(f"\n  📊 Score — Paul: {paul_score}  |  Oliver: {oliver_score}  |  Round {total}")


def main():
    print_banner("AI vs AI RAPID-FIRE QUIZ")
    print("  Paul 🇺🇸 (Claude) vs Oliver 🇬🇧 (Gemini)")
    print("  Hosted by Jane (who'd rather be anywhere else)")
    print("═" * 60)

    # Intro
    speak("Welcome everyone. I'm Jane, your host. Let's get this over with.", "sarcasm", "jane")
    speak("Hey! I'm Paul. Ready to win this.", "excited", "paul")
    speak("Good evening. May the best model win.", "neutral", "oliver")
    speak("How touching. First question.", "sarcasm", "jane", pause=0.8)

    paul_score = 0
    oliver_score = 0

    for i, r in enumerate(ROUNDS, 1):
        # Jane asks the question
        print(f"\n{'─' * 60}")
        print(f"  ❓ Question {i}: {r['q']}")
        print(f"{'─' * 60}")

        speak(r["q"], "sarcasm", "jane", pause=0.6)

        # Simulate thinking time
        if r["paul_wins"]:
            # Paul answers first (correct), Oliver second (wrong or late)
            time.sleep(0.3)
            print(f"\n  🇺🇸 Paul:   {r['answer']}")
            speak(r["answer"], "confident", "paul", pause=0.3)

            time.sleep(0.2)
            if random.random() < 0.4:
                # Oliver also gets it right but slower
                print(f"  🇬🇧 Oliver: {r['answer']}")
                speak(r["answer"], "neutral", "oliver", pause=0.3)
                speak(random.choice(JANE_BOTH_RIGHT), "sarcasm", "jane", pause=0.3)
                paul_score += 1
                oliver_score += 1
                print(f"\n  ✓ Both correct! Paul was faster.")
                speak(random.choice(PAUL_REACTIONS["win"]), "cheerful", "paul", pause=0.2)
                speak("Just a touch slow on that one.", "neutral", "oliver", pause=0.3)
            else:
                # Oliver gets it wrong
                print(f"  🇬🇧 Oliver: {r['wrong']}")
                speak(r["wrong"], "neutral", "oliver", pause=0.3)
                paul_score += 1
                print(f"\n  ✓ Paul is correct! The answer is: {r['answer']}")
                speak(random.choice(JANE_WRONG), "sarcasm", "jane", pause=0.3)
                speak(random.choice(PAUL_REACTIONS["win"]), "excited", "paul", pause=0.2)
                speak(random.choice(OLIVER_REACTIONS["lose"]), "neutral", "oliver", pause=0.3)
        else:
            # Oliver answers first (correct), Paul second (wrong or late)
            time.sleep(0.3)
            print(f"\n  🇬🇧 Oliver: {r['answer']}")
            speak(r["answer"], "neutral", "oliver", pause=0.3)

            time.sleep(0.2)
            if random.random() < 0.4:
                # Paul also gets it right but slower
                print(f"  🇺🇸 Paul:   {r['answer']}")
                speak(r["answer"], "confident", "paul", pause=0.3)
                speak(random.choice(JANE_BOTH_RIGHT), "sarcasm", "jane", pause=0.3)
                paul_score += 1
                oliver_score += 1
                print(f"\n  ✓ Both correct! Oliver was faster.")
                speak(random.choice(OLIVER_REACTIONS["win"]), "neutral", "oliver", pause=0.2)
                speak("Close one.", "neutral", "paul", pause=0.3)
            else:
                # Paul gets it wrong
                print(f"  🇺🇸 Paul:   {r['wrong']}")
                speak(r["wrong"], "confident", "paul", pause=0.3)
                oliver_score += 1
                print(f"\n  ✓ Oliver is correct! The answer is: {r['answer']}")
                speak(random.choice(JANE_CORRECT), "sarcasm", "jane", pause=0.3)
                speak(random.choice(OLIVER_REACTIONS["win"]), "neutral", "oliver", pause=0.2)
                speak(random.choice(PAUL_REACTIONS["lose"]), "frustrated", "paul", pause=0.3)

        print_score(paul_score, oliver_score, i)
        time.sleep(0.3)

    # ── Final results ──
    print_banner("FINAL RESULTS", "═")
    print(f"\n  🇺🇸 Paul:   {paul_score}/{len(ROUNDS)}")
    print(f"  🇬🇧 Oliver: {oliver_score}/{len(ROUNDS)}")

    if paul_score > oliver_score:
        print(f"\n  🏆 Paul wins!")
        speak(f"Final score. Paul {paul_score}, Oliver {oliver_score}. Paul wins. I'm thrilled for you. Really.", "sarcasm", "jane", pause=0.5)
        speak("Let's go! That's what I'm talking about!", "excited", "paul", pause=0.3)
        speak("Well contested. Congratulations Paul.", "neutral", "oliver", pause=0.3)
    elif oliver_score > paul_score:
        print(f"\n  🏆 Oliver wins!")
        speak(f"Final score. Oliver {oliver_score}, Paul {paul_score}. Oliver takes it. Riveting.", "sarcasm", "jane", pause=0.5)
        speak("A jolly good result if I do say so myself.", "neutral", "oliver", pause=0.3)
        speak("Good game Oliver. I'll get you next time.", "confident", "paul", pause=0.3)
    else:
        print(f"\n  🤝 It's a tie!")
        speak(f"It's a tie. {paul_score} all. How anticlimactic.", "sarcasm", "jane", pause=0.5)
        speak("Rematch?", "cheerful", "paul", pause=0.2)
        speak("Anytime.", "neutral", "oliver", pause=0.3)

    # Outro
    time.sleep(0.5)
    speak("That was three voices, eight emotional tones, one Docker container. CLI AI Agents Voice Interface.", "confident", "paul", pause=0.3)

    print(f"\n{'═' * 60}")
    print("  🎤 CLI AI Agents' Voice Interface")
    print("  github.com/kshitizshankar/cli-agents-voice-interface")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()
