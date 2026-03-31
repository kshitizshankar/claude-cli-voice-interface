import httpx, json, os

resp = httpx.get(
    "https://api.mistral.ai/v1/audio/voices",
    headers={"Authorization": f"Bearer {os.environ['MISTRAL_API_KEY']}"},
    params={"page_size": 100},
    timeout=30.0,
)
voices = resp.json()["items"]
# Filter for Poly
for v in voices:
    name = v["name"]
    if "poly" in name.lower() or "Poly" in name:
        langs = ",".join(v.get("languages", []))
        tags = ",".join(v.get("tags", []))
        age = v.get("age", "?")
        vid = v["id"]
        print(f"{name:35s} | {v['gender']:6s} | {langs:10s} | {tags:40s} | {vid}")

print(f"\n--- Total voices: {len(voices)} ---")
print("\nAll unique name prefixes:")
prefixes = sorted(set(v["name"].split(" - ")[0] for v in voices))
for p in prefixes:
    print(f"  {p}")
