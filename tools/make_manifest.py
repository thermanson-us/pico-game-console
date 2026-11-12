#!/usr/bin/env python3
"""make_manifest.py - run on your PC before every git push.

Scans the device folder, writes device/manifest.json with the size + SHA-256 of every file
the Pico should have, and bumps the version number. The Pico downloads the files whose
hash changed the next time it boots.

    python tools/make_manifest.py            # bump version and rewrite the manifest
    python tools/make_manifest.py --check    # just show what changed, write nothing
"""
import hashlib, json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "device")
MANIFEST = "manifest.json"
# never shipped over the air
EXCLUDE_NAMES = {MANIFEST, "main.py", "config.py", "config.example.py", "version.json",
                 "ota_pending.json", "echo_best.txt"}
EXCLUDE_EXT = (".new", ".bak", ".md", ".pyc")

def files():
    out = []
    for d, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(x for x in dirs if not x.startswith((".", "__")))
        for n in sorted(names):
            if n.startswith(".") or n in EXCLUDE_NAMES or n.endswith(EXCLUDE_EXT):
                continue
            full = os.path.join(d, n)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            data = open(full, "rb").read()
            out.append({"path": rel, "size": len(data),
                        "sha256": hashlib.sha256(data).hexdigest()})
    return out

def main():
    mpath = os.path.join(ROOT, MANIFEST)
    old = {"version": 0, "files": []}
    if os.path.exists(mpath):
        old = json.load(open(mpath))
    new_files = files()
    old_map = {f["path"]: f["sha256"] for f in old["files"]}
    changed = [f["path"] for f in new_files if old_map.get(f["path"]) != f["sha256"]]
    removed = [p for p in old_map if p not in {f["path"] for f in new_files}]

    print("Changed/new:", ", ".join(changed) or "none")
    if removed:
        print("No longer shipped (left on the Pico):", ", ".join(removed))
    if "--check" in sys.argv:
        return
    if not changed and not removed:
        print("Nothing changed - manifest left at version", old["version"])
        return
    man = {"version": int(old["version"]) + 1, "files": new_files}
    with open(mpath, "w") as f:
        json.dump(man, f, indent=1)
    print("Wrote %s  version %d  (%d files)" % (mpath, man["version"], len(new_files)))

if __name__ == "__main__":
    main()
