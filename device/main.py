# main.py - boot entry point. Kept tiny on purpose and NEVER replaced by OTA updates,
# so a bad update to any other file can always be fixed by pushing a new version.
#
#   1. ota.run()      - join WiFi, pull any newer files from GitHub, reboot if updated
#   2. import launcher - the game menu
#
# Hold a finger on the screen while it powers up to skip the update check.

import sys

try:
    import ota
    ota.run()
except Exception as e:
    print("OTA error (continuing):")
    sys.print_exception(e)

import launcher
