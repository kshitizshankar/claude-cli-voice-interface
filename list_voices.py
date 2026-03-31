import httpx, json, os

resp = httpx.get(
    "https://api.mistral.ai/v1/audio/voices",
    headers={"Authorization": f"Bearer {os.environ['MISTRAL_API_KEY']}"},
    timeout=30.0,
)
voices = resp.json()["items"]
for v in voices:
    langs = ",".join(v.get("languages", []))
    tags = ",".join(v.get("tags", []))
    name = v["name"]
    gender = v["gender"]
    age = v.get("age", "?")
    vid = v["id"]
    print(f"{name:35s} | {gender:6s} | age:{age} | {langs:20s} | {tags:40s} | {vid}")
