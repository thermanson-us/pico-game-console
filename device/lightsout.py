# lightsout.py - Lights Out puzzle (launched from launcher.py)
#
# Tap a light to flip it and its four neighbours. Turn every light off.
# Each level scrambles a few more lights. PAR is the number of presses used to scramble,
# so it can always be matched (sometimes beaten). Your level is saved on the Pico.

from hw import (display, C, shade, WHITE, GREY,
                wait_for_tap, wait_release, draw_bevel, draw_gradient,
                draw_centered_text, draw_text_centered_in, draw_button)
import time
import random

NAME = "LIGHTS"
SAVE_FILE = "lights_level.txt"

N = 5
CELL, GAP = 40, 4
GX, GY = 8, 12                        # grid top-left (grid is 216 x 216)
PX, PW = 232, 84                      # side panel
BG_RGB = (14, 16, 34)
BG = C(*BG_RGB)
ON_RGB = (255, 205, 60)
OFF_RGB = (40, 46, 78)
GREEN = C(80, 230, 110)
YELLOW = C(255, 220, 60)
BTN_TOP = (PX, 150, PW, 36)           # RESET during play, NEXT after solving
BTN_MENU = (PX, 194, PW, 36)

# ---------------------------------------------------------------- helpers
def cell_rect(r, c):
    return GX + c * (CELL + GAP), GY + r * (CELL + GAP)

def cell_at(px, py):
    c = (px - GX) // (CELL + GAP)
    r = (py - GY) // (CELL + GAP)
    if 0 <= r < N and 0 <= c < N:
        x, y = cell_rect(r, c)
        if x <= px < x + CELL and y <= py < y + CELL:
            return r, c
    return None

def inside(b, px, py):
    x, y, w, h = b
    return x <= px < x + w and y <= py < y + h

def neighbours(r, c):
    out = []
    for dr, dc in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < N and 0 <= cc < N:
            out.append((rr, cc))
    return out

def toggle(grid, r, c):
    for rr, cc in neighbours(r, c):
        grid[rr][cc] ^= 1

def solved(grid):
    for row in grid:
        for v in row:
            if v:
                return False
    return True

def make_puzzle(level):
    """Scramble from all-off with distinct random presses. Returns (grid, presses)."""
    count = min(2 + level, 15)
    cells = [(r, c) for r in range(N) for c in range(N)]
    while True:
        for i in range(len(cells) - 1, 0, -1):
            j = random.randint(0, i)
            cells[i], cells[j] = cells[j], cells[i]
        presses = cells[:count]
        grid = [[0] * N for _ in range(N)]
        for r, c in presses:
            toggle(grid, r, c)
        if not solved(grid):
            return grid, presses

def load_level():
    try:
        with open(SAVE_FILE) as f:
            return max(1, int(f.read().strip()))
    except (OSError, ValueError):
        return 1

def save_level(n):
    try:
        with open(SAVE_FILE, "w") as f:
            f.write(str(n))
    except OSError:
        pass

# ---------------------------------------------------------------- drawing
def draw_cell(on, r, c):
    x, y = cell_rect(r, c)
    rgb = ON_RGB if on else OFF_RGB
    display.fill_rectangle(x, y, CELL, CELL, C(*rgb))
    draw_bevel(x, y, CELL, CELL, rgb, 0.45, -0.45)
    cx, cy = x + CELL // 2, y + CELL // 2
    if on:
        display.fill_circle(cx, cy, 11, C(*shade(rgb, 0.45)))
        display.fill_circle(cx - 3, cy - 3, 4, WHITE)
    else:
        display.fill_circle(cx, cy, 6, C(*shade(rgb, -0.35)))

def draw_grid(grid):
    for r in range(N):
        for c in range(N):
            draw_cell(grid[r][c], r, c)

def draw_moves(moves, par):
    display.fill_rectangle(PX, 90, PW, 24, BG)
    draw_text_centered_in(PX, PW, 90, str(moves), YELLOW if moves > par else WHITE, BG)

def draw_panel(level, moves, par):
    display.fill_rectangle(PX, 0, PW, 148, BG)
    draw_text_centered_in(PX, PW, 6, "LEVEL", GREY, BG)
    draw_text_centered_in(PX, PW, 30, str(level), WHITE, BG)
    draw_text_centered_in(PX, PW, 66, "MOVES", GREY, BG)
    draw_moves(moves, par)
    draw_text_centered_in(PX, PW, 120, "PAR %d" % par, GREY, BG)

def draw_screen(grid, level, moves, par):
    display.clear(BG)
    draw_grid(grid)
    draw_panel(level, moves, par)
    draw_button(*BTN_TOP, "RESET", (90, 70, 40))
    draw_button(*BTN_MENU, "MENU", (70, 80, 150))

def celebrate(grid):
    # ripple out from the centre: light up, then off again
    for d in range(N):
        for r in range(N):
            for c in range(N):
                if max(abs(r - 2), abs(c - 2)) == d:
                    draw_cell(1, r, c)
        time.sleep(0.04)
    for d in range(N):
        for r in range(N):
            for c in range(N):
                if max(abs(r - 2), abs(c - 2)) == d:
                    draw_cell(0, r, c)
        time.sleep(0.04)

# ---------------------------------------------------------------- game
def play_level(level):
    """Returns 'next' or 'menu'."""
    grid, presses = make_puzzle(level)
    start = [row[:] for row in grid]
    par = len(presses)
    moves = 0
    draw_screen(grid, level, moves, par)
    while True:
        px, py = wait_for_tap()
        if inside(BTN_MENU, px, py):
            wait_release()
            return "menu"
        if inside(BTN_TOP, px, py):
            wait_release()
            grid = [row[:] for row in start]
            moves = 0
            draw_grid(grid)
            draw_moves(moves, par)
            continue
        rc = cell_at(px, py)
        if rc is None:
            continue
        r, c = rc
        toggle(grid, r, c)
        for rr, cc in neighbours(r, c):
            draw_cell(grid[rr][cc], rr, cc)
        moves += 1
        draw_moves(moves, par)
        if solved(grid):
            break

    # solved - remember progress right away, even if the player goes back to the menu
    save_level(level + 1)
    celebrate(grid)
    bx, by, bw, bh = GX + 18, GY + 64, 180, 88
    display.fill_rectangle(bx + 3, by + 3, bw, bh, C(4, 4, 8))
    display.fill_rectangle(bx, by, bw, bh, C(24, 30, 60))
    draw_bevel(bx, by, bw, bh, (24, 30, 60), 0.4, -0.5)
    draw_text_centered_in(bx, bw, by + 14, "SOLVED!", GREEN, C(24, 30, 60))
    msg = "PAR!" if moves <= par else "%d MOVES" % moves
    draw_text_centered_in(bx, bw, by + 48, msg, YELLOW if moves <= par else WHITE, C(24, 30, 60))
    draw_button(*BTN_TOP, "NEXT", (40, 140, 70))
    while True:
        px, py = wait_for_tap()
        if inside(BTN_TOP, px, py):
            wait_release()
            return "next"
        if inside(BTN_MENU, px, py):
            wait_release()
            return "menu"

def title_screen(level):
    draw_gradient(0, 0, 320, 240)
    draw_centered_text(24, "LIGHTS OUT", WHITE, C(18, 22, 50))
    # little 5x5 logo with a plus-shaped group lit
    lit = {(1, 2), (2, 1), (2, 2), (2, 3), (3, 2)}
    for r in range(N):
        for c in range(N):
            x, y = 110 + c * 21, 62 + r * 21
            on = (r, c) in lit
            display.fill_rectangle(x, y, 18, 18, C(*(ON_RGB if on else OFF_RGB)))
            if on:
                display.fill_circle(x + 9, y + 9, 4, C(*shade(ON_RGB, 0.5)))
    draw_centered_text(172, "TURN EVERY LIGHT OFF", GREY, C(5, 6, 14))
    draw_centered_text(204, "TAP TO START  LV %d" % level, C(255, 220, 60), C(1, 1, 3))
    wait_for_tap()
    wait_release()

# ---------------------------------------------------------------- entry points
def run():
    level = load_level()
    title_screen(level)
    while True:
        if play_level(level) == "menu":
            return
        level += 1

def preview(x, y, w, h):
    """Mini picture for the launcher tile."""
    s, g = 11, 2
    gx = x + (w - (N * s + (N - 1) * g)) // 2
    gy = y + (h - (N * s + (N - 1) * g)) // 2
    lit = {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (3, 3), (3, 4), (4, 3), (2, 4)}
    for r in range(N):
        for c in range(N):
            on = (r, c) in lit
            display.fill_rectangle(gx + c * (s + g), gy + r * (s + g), s, s,
                                   C(*(ON_RGB if on else OFF_RGB)))
