# config.py - WiFi + update settings. Copy this file to the Pico as  config.py  and fill it in.
# config.py is never sent over the air and should NOT be committed to GitHub (it's in .gitignore).

WIFI_SSID = "your-network-name"
WIFI_PASSWORD = "your-wifi-password"
WIFI_COUNTRY = "US"

GITHUB_OWNER = "your-github-username"
GITHUB_REPO = "your-repo-name"
GITHUB_BRANCH = "main"
GITHUB_PATH = "device"          # folder in the repo that mirrors the Pico's files ("" = repo root)
GITHUB_TOKEN = ""               # only for a PRIVATE repo: a fine-grained token with read-only Contents access

OTA_ENABLED = True
WIFI_TIMEOUT_S = 10
