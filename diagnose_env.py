"""
Standalone .env diagnostic - run this directly to check
if python-dotenv can read your .env file at all, completely
separate from the rest of the app.

Run from the project root:
  .venv\\Scripts\\python.exe diagnose_env.py
"""

import os

print("Current working directory:", os.getcwd())
print()

env_path = os.path.join(os.getcwd(), ".env")
print(".env expected at:", env_path)
print(".env exists:", os.path.exists(env_path))
print()

if os.path.exists(env_path):
    print("Raw file size (bytes):", os.path.getsize(env_path))
    with open(env_path, "rb") as f:
        raw_bytes = f.read(50)
        print("First 50 bytes (raw):", raw_bytes)
    print()

from dotenv import load_dotenv
result = load_dotenv(env_path)
print("load_dotenv() returned:", result, "(True means it found and parsed the file)")
print()

token = os.getenv("WHATSAPP_ACCESS_TOKEN")
if token:
    print("WHATSAPP_ACCESS_TOKEN found. Length:", len(token))
    print("First 10 chars:", token[:10])
else:
    print("WHATSAPP_ACCESS_TOKEN is None/empty - dotenv did not find it.")