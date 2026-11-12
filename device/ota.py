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

# "EMMA" glides across the bottom of the CHECKING UPDATES screen
EMMA_TEXT = "EMMA"
EMMA_RGB = (255, 105, 180)    # pink
EMMA_SCALE = 2                # 2 = double size (48 px tall)
EMMA_Y = 178                  # below the status text
EMMA_STEP = 2                 # pixels per frame
EMMA_FRAME_MS = 25            # 2 px every 25 ms = 80 px/s, about 5.3 s from off-left to off-right

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
        self.emma = None
        try:
            import hw
            self.hw = hw
        except Exception as e:
            print("OTA: no display:", e)
            self.hw = None

    # ---- gliding name -------------------------------------------------------------
    def emma_start(self):
        try:
            self._emma_start()
        except Exception as e:
            print("OTA: EMMA disabled:", e)
            self.emma = None

    def _emma_start(self):
        """Pre-render the text once at EMMA_SCALE (with EMMA_STEP black columns in front, which
        wipe the previous position as it moves). It starts fully off the left edge."""
        if not self.hw:
            return
        h = self.hw
        color = h.C(*EMMA_RGB)
        k = EMMA_SCALE
        pad = EMMA_STEP
        tw = h.text_w(EMMA_TEXT)
        th = h.font.height
        # 1x render
        small = bytearray(tw * th * 2)
        x = 0
        for ch in EMMA_TEXT:
            b, cw, chh = h.font.get_letter(ch, color, 0)
            for row in range(chh):
                d = (row * tw + x) * 2
                small[d:d + cw * 2] = b[row * cw * 2:(row + 1) * cw * 2]
            x += cw + 1
        # scale up k x k
        W = pad + tw * k
        H = th * k
        buf = bytearray(W * H * 2)                    # zeros = black
        for row in range(th):
            line = bytearray(W * 2)
            for col in range(tw):
                i = (row * tw + col) * 2
                hi, lo = small[i], small[i + 1]
                if hi or lo:
                    d = (pad + col * k) * 2
                    for j in range(k):
                        line[d + 2 * j] = hi
                        line[d + 2 * j + 1] = lo
            for j in range(k):
                d = (row * k + j) * W * 2
                buf[d:d + W * 2] = line
        self.emma = [buf, W, H, -W, time.ticks_ms()]   # completely off the left edge
        self._emma_draw()

    def _emma_draw(self):
        buf, W, H, ex, _ = self.emma
        x0 = max(0, ex)
        x1 = min(320, ex + W)
        cw = x1 - x0
        if cw <= 0:
            return
        off = x0 - ex
        if off == 0 and cw == W:
            data = buf
        else:                                          # clip at the screen edges
            data = bytearray(cw * H * 2)
            for row in range(H):
                s0 = (row * W + off) * 2
                data[row * cw * 2:(row + 1) * cw * 2] = buf[s0:s0 + cw * 2]
        self.hw.display.blit(x0, EMMA_Y, cw, H, data)

    def emma_tick(self):
        try:
            return self._emma_tick()
        except Exception as e:
            print("OTA: EMMA disabled:", e)
            self.emma = None
            return False

    def _emma_tick(self):
        """Advance one frame if it's time. Returns False once the text is off the right edge."""
        if not self.emma:
            return False
        now = time.ticks_ms()
        if time.ticks_diff(now, self.emma[4]) < EMMA_FRAME_MS:
            return True
        self.emma[4] = now
        self.emma[3] += EMMA_STEP
        self._emma_draw()
        if self.emma[3] + EMMA_STEP >= 320:            # only the black lead-in is left on screen
            self.emma = None
            return False
        return True

    def emma_finish(self):
        """Let the glide run to the right edge before the screen changes."""
        while self.emma_tick():
            time.sleep_ms(5)

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
def _connect(cfg, ui=None):
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
            for _ in range(20):                      # ~200 ms, animating the name meanwhile
                if ui:
                    ui.emma_tick()
                time.sleep_ms(10)
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
    ui.emma_start()
    wlan = _connect(config, ui)
    ui.emma_finish()
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
