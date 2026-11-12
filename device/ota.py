# ota.py - pull-mode over-the-air updates from a GitHub repo
#
# At boot (called from main.py):
#   - joins WiFi (config.py), fetches <repo>/<GITHUB_PATH>/manifest.json
#   - if the manifest version is newer than version.json on the Pico, downloads every file
#     whose SHA-256 differs, each to <file>.new, verifying size + hash
#   - only when ALL files verified: records the swap in ota_pending.json, renames the .new
#     files into place, writes version.json, reboots
#   - any failure (no WiFi, GitHub down, bad hash) -> deletes the .new files, boots the old code
# If power is lost mid-swap, the next boot finishes the swap from ota_pending.json.
# main.py and config.py are never touched.

import os, json, time, gc, sys, machine, binascii, hashlib

VERSION_FILE = "version.json"
PENDING_FILE = "ota_pending.json"
PROTECTED = ("main.py", "config.py")
CHUNK = 1024

# ---------------------------------------------------------------- file helpers
def _exists(p):
    try:
        os.stat(p)
        return True
    except OSError:
        return False

def _makedirs_for(path):
    cur = ""
    for part in path.split("/")[:-1]:
        cur = cur + "/" + part if cur else part
        if not _exists(cur):
            os.mkdir(cur)

def _sha256_file(path):
    h = hashlib.sha256()
    buf = bytearray(CHUNK)
    mv = memoryview(buf)
    with open(path, "rb") as f:
        while True:
            n = f.readinto(buf)
            if not n:
                break
            h.update(mv[:n])
    return binascii.hexlify(h.digest()).decode()

def local_version():
    try:
        with open(VERSION_FILE) as f:
            return int(json.load(f).get("version", 0))
    except (OSError, ValueError):
        return 0

def finish_pending():
    """Complete a swap that was interrupted (e.g. power loss)."""
    if not _exists(PENDING_FILE):
        return False
    with open(PENDING_FILE) as f:
        info = json.load(f)
    for p in info["files"]:
        if _exists(p + ".new"):
            if _exists(p):
                os.remove(p)
            os.rename(p + ".new", p)
    with open(VERSION_FILE, "w") as f:
        json.dump({"version": info["version"]}, f)
    os.remove(PENDING_FILE)
    return True

def _cleanup_new(paths):
    for p in paths:
        try:
            os.remove(p + ".new")
        except OSError:
            pass

# ---------------------------------------------------------------- screen
class _UI:
    def __init__(self):
        try:
            import hw
            self.hw = hw
        except Exception as e:
            print("OTA: no display:", e)
            self.hw = None

    def msg(self, line1, line2="", color=None):
        print("OTA:", line1, line2)
        if not self.hw:
            return
        h = self.hw
        h.display.clear(h.BLACK)
        h.draw_centered_text(80, line1, color or h.WHITE)
        if line2:
            h.draw_centered_text(120, line2[:24], h.GREY)

    def progress(self, i, n, name):
        print("OTA: %d/%d %s" % (i + 1, n, name))
        if not self.hw:
            return
        h = self.hw
        h.display.fill_rectangle(0, 120, 320, 24, h.BLACK)
        h.draw_centered_text(120, name[-24:], h.GREY)
        w = 260
        h.display.fill_rectangle(30, 170, w, 12, h.C(40, 40, 60))
        h.display.fill_rectangle(30, 170, int(w * (i + 1) / n), 12, h.C(60, 160, 255))

    def touched(self):
        if not self.hw:
            return False
        return self.hw.read_touch_filtered() is not None

# ---------------------------------------------------------------- network
def _connect(cfg):
    import network
    try:
        import rp2
        rp2.country(getattr(cfg, "WIFI_COUNTRY", "US"))
    except Exception:
        pass
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(cfg.WIFI_SSID, cfg.WIFI_PASSWORD)
        t0 = time.ticks_ms()
        limit = int(getattr(cfg, "WIFI_TIMEOUT_S", 10) * 1000)
        while not wlan.isconnected():
            if wlan.status() < 0 or time.ticks_diff(time.ticks_ms(), t0) > limit:
                print("OTA: WiFi failed, status", wlan.status())
                wlan.active(False)
                return None
            time.sleep_ms(200)
    print("OTA: WiFi", wlan.ifconfig()[0])
    return wlan

class _Repo:
    def __init__(self, cfg):
        path = getattr(cfg, "GITHUB_PATH", "")
        self.base = "https://raw.githubusercontent.com/%s/%s/%s/%s" % (
            cfg.GITHUB_OWNER, cfg.GITHUB_REPO, getattr(cfg, "GITHUB_BRANCH", "main"),
            (path.strip("/") + "/") if path else "")
        self.headers = {"User-Agent": "pico-ota"}
        token = getattr(cfg, "GITHUB_TOKEN", "")
        if token:
            self.headers["Authorization"] = "token " + token

    def _get(self, rel, stream=False):
        import requests
        r = requests.get(self.base + rel, headers=self.headers, stream=stream)
        if r.status_code != 200:
            r.close()
            raise OSError("HTTP %d for %s" % (r.status_code, rel))
        return r

    def manifest(self):
        # unique query string so GitHub's cache hands back the latest commit
        r = self._get("manifest.json?t=%d" % time.ticks_ms())
        try:
            return r.json()
        finally:
            r.close()

    def download(self, entry):
        path = entry["path"]
        tmp = path + ".new"
        _makedirs_for(path)
        h = hashlib.sha256()
        size = 0
        r = self._get(path, stream=True)
        try:
            with open(tmp, "wb") as f:
                while True:
                    chunk = r.raw.read(CHUNK)
                    if not chunk:
                        break
                    f.write(chunk)
                    h.update(chunk)
                    size += len(chunk)
        finally:
            r.close()
        digest = binascii.hexlify(h.digest()).decode()
        if size != entry["size"] or digest != entry["sha256"]:
            raise ValueError("verify failed for %s (%d bytes)" % (path, size))

# ---------------------------------------------------------------- main entry
def run():
    if finish_pending():
        print("OTA: finished an interrupted update")
    try:
        import config
    except ImportError:
        print("OTA: no config.py - skipping")
        return
    if not getattr(config, "OTA_ENABLED", True):
        return

    ui = _UI()
    if ui.touched():
        ui.msg("UPDATE SKIPPED")
        time.sleep(0.6)
        return

    local = local_version()
    ui.msg("CHECKING UPDATES", "v%d - %s" % (local, config.WIFI_SSID))
    wlan = _connect(config)
    if wlan is None:
        ui.msg("NO WIFI", "starting offline")
        time.sleep(1)
        return

    todo = []
    try:
        repo = _Repo(config)
        man = repo.manifest()
        remote = int(man["version"])
        if remote <= local:
            ui.msg("UP TO DATE", "v%d" % local)
            time.sleep(0.6)
            return
        # only files that actually changed
        for entry in man["files"]:
            p = entry["path"]
            if p in PROTECTED:
                continue
            if _exists(p) and _sha256_file(p) == entry["sha256"]:
                continue
            todo.append(entry)
        ui.msg("UPDATING TO v%d" % remote)
        for i, entry in enumerate(todo):
            ui.progress(i, len(todo), entry["path"])
            repo.download(entry)
            gc.collect()
        # everything verified -> swap in
        with open(PENDING_FILE, "w") as f:
            json.dump({"version": remote, "files": [e["path"] for e in todo]}, f)
        finish_pending()
        ui.msg("UPDATED TO v%d" % remote, "%d files - restarting" % len(todo), ui.hw and ui.hw.C(80, 230, 110))
        time.sleep(1.2)
        machine.reset()
    except Exception as e:
        sys.print_exception(e)
        _cleanup_new([e2["path"] for e2 in todo])
        ui.msg("UPDATE FAILED", "starting current version", ui.hw and ui.hw.C(230, 60, 60))
        time.sleep(1.5)
    finally:
        try:
            wlan.disconnect()
            wlan.active(False)      # save battery
        except Exception:
            pass
