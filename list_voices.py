#!/usr/bin/env python3
"""List all available Voxtral TTS preset voices with details.

Usage: MISTRAL_API_KEY=your-key python3 list_voices.py
"""
import httpx
import os
import sys

api_key = os.environ.get("MISTRAL_API_KEY")
if not api_key:
    print("Error: MISTRAL_API_KEY not set", file=sys.stderr)
    sys.exit(1)

# Fetch all pages (API paginates at 10 per page)
seen_ids = set()
all_voices = []
page = 1

while True:
    resp = httpx.get(
        "https://api.mistral.ai/v1/audio/voices",
        headers={"Authorization": f"Bearer {api_key}"},
        params={"page_size": 10, "page": page},
        timeout=30.0,
    )
    if resp.status_code != 200:
        print(f"API error {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    for v in data["items"]:
        if v["id"] not in seen_ids:
            seen_ids.add(v["id"])
            all_voices.append(v)

    if page >= data.get("total_pages", 1):
        break
    page += 1

# Display
print(f"Total unique voices: {len(all_voices)}\n")
print(f"{'Name':35s} | {'Gender':6s} | {'Language':10s} | {'Tags':40s} | ID")
print("-" * 130)
for v in sorted(all_voices, key=lambda x: x["name"]):
    name = v["name"]
    gender = v["gender"]
    langs = ",".join(v.get("languages", []))
    tags = ",".join(v.get("tags", []))
    vid = v["id"]
    print(f"{name:35s} | {gender:6s} | {langs:10s} | {tags:40s} | {vid}")

# Summary
print(f"\nVoice characters:")
characters = sorted(set(v["name"].split(" - ")[0] for v in all_voices))
for c in characters:
    tones = [v["name"].split(" - ")[1] for v in all_voices if v["name"].startswith(c + " - ")]
    print(f"  {c}: {', '.join(tones)}")
