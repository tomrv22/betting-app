import os
import requests
import subprocess

TOKEN = os.getenv("TELEGRAM_TOKEN")

print("Checking Telegram updates...")

url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
data = requests.get(url).json()

trigger = False

for update in data.get("result", []):
    message = update.get("message", {})
    text = message.get("text", "").lower()

    if text == "run":
        trigger = True

if trigger:
    print("Trigger detected → running latest-prematch.py")

    subprocess.run(["python", "latest-pre-match.py"], check=True)
else:
    print("No trigger found.")