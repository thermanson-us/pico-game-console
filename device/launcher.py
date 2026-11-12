# launcher.py - game launcher for the Pico 2 W touchscreen console (started by main.py)
# Four tiles; tap one to start that game. Games return here when you pick MENU.
#
# To add a game: put its module name in a free GAMES slot. The module needs
#   NAME = "SHORT"            label shown on the tile
#   run()                     plays the game, returns when the user picks MENU
#   preview(x, y, w, h)       draws a mini picture inside the tile

from hw import (display, C, shade, BLACK, WHITE, GREY,
                wait_for_tap, wait_release, draw_gradient, draw_bevel,
                draw_text_centered_in)
import time
import sys
import gc

GAMES = ["matchgame", "echogame", "lightsout", "tictactoe"]     # slots 1..4

TILE_W, TILE_H = 150, 108
GAP = 8
X0 = (320 - (2 * TILE_W + GAP)) // 2
Y0 = (240 - (2 * TILE_H + GAP)) // 2
LABEL_H = 30
TILE_RGB = (34, 40, 80)
EMPTY_RGB = (30, 30, 36)

_modules = {}

def tile_rect(i):
    return X0 + (i % 2) * (TILE_W + GAP), Y0 + (i // 2) * (TILE_H + GAP)

def tile_at(px, py):
    for i in range(4):
        x, y = tile_rect(i)
        if x <= px < x + TILE_W and y <= py < y + TILE_H:
            return i
    return None

def load(i):
    name = GAMES[i]
    if name is None:
        return None
    if name not in _modules:
        try:
            _modules[name] = __import__(name)
        except Exception as e:
            print("Could not load", name)
            sys.print_exception(e)
            _modules[name] = None
    return _modules[name]

def draw_tile(i, pressed=False):
    x, y = tile_rect(i)
    mod = load(i)
    rgb = TILE_RGB if mod else EMPTY_RGB
    if pressed:
        rgb = shade(rgb, 0.35)
    display.fill_rectangle(x + 3, y + 3, TILE_W, TILE_H, C(8, 8, 8))
    display.fill_rectangle(x, y, TILE_W, TILE_H, C(*rgb))
    draw_bevel(x, y, TILE_W, TILE_H, rgb, 0.35, -0.5)
    # label strip
    ly = y + TILE_H - LABEL_H
    strip = shade(rgb, -0.35)
    display.fill_rectangle(x + 3, ly, TILE_W - 6, LABEL_H - 3, C(*strip))
    if mod:
        try:
            mod.preview(x + 4, y + 4, TILE_W - 8, TILE_H - LABEL_H - 6)
        except Exception as e:
            sys.print_exception(e)
        label = getattr(mod, "NAME", GAMES[i].upper())
        draw_text_centered_in(x, TILE_W, ly + 2, label, WHITE, C(*strip))
    else:
        # placeholder: big slot number
        num = str(i + 1)
        cx, cy = x + TILE_W // 2, y + (TILE_H - LABEL_H) // 2
        display.fill_circle(cx, cy, 24, C(*shade(rgb, 0.15)))
        draw_text_centered_in(x, TILE_W, cy - 12, num, GREY, C(*shade(rgb, 0.15)))
        draw_text_centered_in(x, TILE_W, ly + 2, "SOON", GREY, C(*strip))

def draw_menu():
    draw_gradient(0, 0, 320, 240)
    for i in range(4):
        draw_tile(i)

def show_error(name):
    display.clear(BLACK)
    draw_text_centered_in(0, 320, 90, "GAME ERROR", C(230, 60, 60), BLACK)
    draw_text_centered_in(0, 320, 130, name or "", GREY, BLACK)
    time.sleep(2)

def main():
    draw_menu()
    while True:
        px, py = wait_for_tap()
        i = tile_at(px, py)
        if i is None:
            continue
        mod = load(i)
        draw_tile(i, pressed=True)
        wait_release()
        if mod is None:
            time.sleep(0.15)
            draw_tile(i)
            continue
        try:
            mod.run()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            sys.print_exception(e)
            show_error(GAMES[i])
        gc.collect()
        draw_menu()

main()
