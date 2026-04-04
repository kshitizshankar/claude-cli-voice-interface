#!/usr/bin/env python3
"""List all available Voxtral TTS voices with full JSON details.

Usage: MISTRAL_API_KEY=your-key python3 list_all_voices.py
"""
import httpx
import json
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

print(json.dumps(all_voices, indent=2))
print(f"\n// Total unique voices: {len(all_voices)}", file=sys.stderr)
