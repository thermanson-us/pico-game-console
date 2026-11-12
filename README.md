# Pico 2 W touchscreen game console

Raspberry Pi Pico 2 W + 2.4" ILI9341 Uno shield (8-bit parallel) + resistive touch, MicroPython.
Games: Memory Match, Echo. Updates itself over WiFi from this repo.

## Layout

```
device/          everything that lives on the Pico (mirrors the Pico's filesystem)
  main.py          boot: OTA check, then the launcher   (never updated over the air)
  config.py        WiFi + repo settings                 (on the Pico only - not in git)
  config.example.py
  ota.py           pull-mode updater
  launcher.py      4-tile game menu
  hw.py            shared display / touch / font setup
  ili9341_par.py   PIO 8-bit parallel ILI9341 + 4-wire touch driver
  xglcd_font.py, fonts/Unispace12x24.c
  matchgame.py, echogame.py
  manifest.json    generated - version + SHA-256 of every file
tools/make_manifest.py
case/pico_game_case.scad
```

## One-time setup on the Pico (USB, Thonny)

1. Copy everything in `device/` to the Pico (same folder structure).
2. Copy `config.example.py` to the Pico as `config.py` and fill in WiFi + repo details.

## Shipping an update

1. Edit files in `device/`.
2. `python tools/make_manifest.py` - bumps the version, records the new hashes.
3. Commit and push (including `device/manifest.json`).
4. Power-cycle the Pico. It shows CHECKING UPDATES, downloads only the changed files,
   verifies each one, swaps them in and restarts.

Hold a finger on the screen during power-up to skip the update check.
If WiFi or GitHub is unreachable, or a download fails verification, the Pico keeps the
current version and boots normally.

## Adding a game

Add `mygame.py` with `NAME`, `run()` and `preview(x, y, w, h)`, put `"mygame"` in a free slot of
`GAMES` in `launcher.py`, run `make_manifest.py`, push.
