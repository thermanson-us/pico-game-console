# tictactoe.py - Tic-Tac-Toe vs the Pico (launched from launcher.py)
#
# You are X (blue), the Pico is O (red). Who starts alternates every game.
# The Pico plays a solid strategy but slips up now and then, so it can be beaten.

from hw import (display, C, shade, WHITE, GREY,
                wait_for_tap, wait_release, draw_bevel, draw_gradient,
                draw_centered_text, draw_text_centered_in, draw_button)
import time
import random

NAME = "TICTACTOE"
MISTAKE_CHANCE = 0.2      # how often the Pico plays a random square instead of its best one

CELL, GAP = 68, 6
GX, GY = 12, 12           # board top-left (board is 216 x 216)
PX, PW = 240, 76          # side panel
BG_RGB = (14, 16, 34)
BG = C(*BG_RGB)
CELL_RGB = (32, 38, 70)
X_RGB = (80, 170, 255)
O_RGB = (255, 105, 90)
GREEN = C(80, 230, 110)
RED = C(255, 90, 80)
YELLOW = C(255, 220, 60)
BTN_NEW = (PX, 150, PW, 36)
BTN_MENU = (PX, 194, PW, 36)

LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))
CORNERS = (0, 2, 6, 8)
SIDES = (1, 3, 5, 7)

# ---------------------------------------------------------------- helpers
def cell_rect(i):
    return GX + (i % 3) * (CELL + GAP), GY + (i // 3) * (CELL + GAP)

def cell_center(i):
    x, y = cell_rect(i)
    return x + CELL // 2, y + CELL // 2

def cell_at(px, py):
    for i in range(9):
        x, y = cell_rect(i)
        if x <= px < x + CELL and y <= py < y + CELL:
            return i
    return None

def inside(b, px, py):
    x, y, w, h = b
    return x <= px < x + w and y <= py < y + h

def winner(b):
    """('X'|'O', line) | ('D', None) for a draw | (None, None) if the game goes on."""
    for a, m, z in LINES:
        if b[a] and b[a] == b[m] == b[z]:
            return b[a], (a, m, z)
    if all(b):
        return "D", None
    return None, None

def _completing(b, who):
    for a, m, z in LINES:
        trio = (b[a], b[m], b[z])
        if trio.count(who) == 2 and trio.count(None) == 1:
            return (a, m, z)[trio.index(None)]
    return None

def cpu_move(b):
    empty = [i for i in range(9) if b[i] is None]
    if random.random() < MISTAKE_CHANCE:
        return random.choice(empty)
    for who in ("O", "X"):                 # win, else block
        i = _completing(b, who)
        if i is not None:
            return i
    if b[4] is None:
        return 4
    for c in CORNERS:                      # opposite corner of the player's
        opp = 8 - c
        if b[c] == "X" and b[opp] is None:
            return opp
    # if the player holds two opposite corners, take a side (stops the classic fork)
    if (b[0] == b[8] == "X" or b[2] == b[6] == "X") and b[4] == "O":
        free = [s for s in SIDES if b[s] is None]
        if free:
            return random.choice(free)
    free = [c for c in CORNERS if b[c] is None]
    if free:
        return random.choice(free)
    return random.choice(empty)

# ---------------------------------------------------------------- drawing
def stroke(x0, y0, x1, y1, r, color, pause=0.0):
    n = max(abs(x1 - x0), abs(y1 - y0)) // 3 + 1
    for k in range(n + 1):
        display.fill_circle(x0 + (x1 - x0) * k // n, y0 + (y1 - y0) * k // n, r, color)
        if pause and k % 4 == 0:
            time.sleep(pause)

def draw_cell(i, highlight=False):
    x, y = cell_rect(i)
    rgb = shade(CELL_RGB, 0.25) if highlight else CELL_RGB
    display.fill_rectangle(x, y, CELL, CELL, C(*rgb))
    draw_bevel(x, y, CELL, CELL, rgb, 0.35, -0.45)

def draw_x(i, animate=True):
    cx, cy = cell_center(i)
    d = 18
    col, glow = C(*X_RGB), C(*shade(X_RGB, 0.5))
    p = 0.01 if animate else 0
    stroke(cx - d, cy - d, cx + d, cy + d, 5, col, p)
    stroke(cx + d, cy - d, cx - d, cy + d, 5, col, p)
    display.fill_circle(cx, cy, 3, glow)

def draw_o(i, bg_rgb=CELL_RGB):
    cx, cy = cell_center(i)
    display.fill_circle(cx, cy, 24, C(*O_RGB))
    display.fill_circle(cx, cy, 17, C(*bg_rgb))
    display.fill_circle(cx - 12, cy - 13, 3, C(*shade(O_RGB, 0.55)))

def draw_mark(b, i, highlight=False, animate=False):
    bg = shade(CELL_RGB, 0.25) if highlight else CELL_RGB
    draw_cell(i, highlight)
    if b[i] == "X":
        draw_x(i, animate)
    elif b[i] == "O":
        draw_o(i, bg)

def draw_scores(score):
    display.fill_rectangle(PX, 0, PW, 92, BG)
    draw_text_centered_in(PX, PW, 6, "W %d" % score["W"], GREEN, BG)
    draw_text_centered_in(PX, PW, 34, "L %d" % score["L"], RED, BG)
    draw_text_centered_in(PX, PW, 62, "D %d" % score["D"], GREY, BG)

def draw_status(text, color):
    display.fill_rectangle(PX, 100, PW, 40, BG)
    draw_text_centered_in(PX, PW, 108, text, color, BG)

def draw_board_screen(score):
    display.clear(BG)
    for i in range(9):
        draw_cell(i)
    draw_scores(score)
    draw_button(*BTN_NEW, "NEW", (40, 140, 70))
    draw_button(*BTN_MENU, "MENU", (70, 80, 150))

# ---------------------------------------------------------------- game
def play(first, score):
    """One game. Returns 'new' or 'menu'."""
    b = [None] * 9
    draw_board_screen(score)
    turn = first
    while True:
        w, line = winner(b)
        if w:
            break
        if turn == "X":
            draw_status("YOU", C(*X_RGB))
            while True:
                px, py = wait_for_tap()
                if inside(BTN_MENU, px, py):
                    wait_release()
                    return "menu"
                if inside(BTN_NEW, px, py):
                    wait_release()
                    return "new"
                i = cell_at(px, py)
                if i is not None and b[i] is None:
                    break
            b[i] = "X"
            draw_x(i)
            turn = "O"
        else:
            draw_status("CPU", C(*O_RGB))
            time.sleep(0.35)
            i = cpu_move(b)
            b[i] = "O"
            draw_o(i)
            turn = "X"

    # game over
    if w == "X":
        score["W"] += 1
        draw_status("WIN!", GREEN)
    elif w == "O":
        score["L"] += 1
        draw_status("LOSE", RED)
    else:
        score["D"] += 1
        draw_status("DRAW", GREY)
    draw_scores(score)
    if line:
        for _ in range(2):
            for i in line:
                draw_mark(b, i, highlight=True)
            time.sleep(0.15)
            for i in line:
                draw_mark(b, i)
            time.sleep(0.1)
        for i in line:
            draw_mark(b, i, highlight=True)
        x0, y0 = cell_center(line[0])
        x1, y1 = cell_center(line[2])
        stroke(x0, y0, x1, y1, 3, YELLOW, 0.005)
    while True:
        px, py = wait_for_tap()
        if inside(BTN_MENU, px, py):
            wait_release()
            return "menu"
        if inside(BTN_NEW, px, py) or cell_at(px, py) is not None:
            wait_release()
            return "new"

def title_screen():
    draw_gradient(0, 0, 320, 240)
    draw_centered_text(24, "TIC TAC TOE", WHITE, C(18, 22, 50))
    # mini board logo
    s, g = 30, 4
    x0, y0 = 160 - (3 * s + 2 * g) // 2, 64
    marks = {0: "X", 4: "O", 8: "X", 2: "O"}
    for i in range(9):
        x, y = x0 + (i % 3) * (s + g), y0 + (i // 3) * (s + g)
        display.fill_rectangle(x, y, s, s, C(*CELL_RGB))
        cx, cy = x + s // 2, y + s // 2
        if marks.get(i) == "X":
            stroke(cx - 8, cy - 8, cx + 8, cy + 8, 2, C(*X_RGB))
            stroke(cx + 8, cy - 8, cx - 8, cy + 8, 2, C(*X_RGB))
        elif marks.get(i) == "O":
            display.fill_circle(cx, cy, 10, C(*O_RGB))
            display.fill_circle(cx, cy, 6, C(*CELL_RGB))
    draw_centered_text(176, "YOU ARE X", C(*X_RGB), C(4, 5, 12))
    draw_centered_text(206, "TAP TO START", GREY, C(1, 1, 3))
    wait_for_tap()
    wait_release()

# ---------------------------------------------------------------- entry points
def run():
    title_screen()
    score = {"W": 0, "L": 0, "D": 0}
    first = "X"
    while play(first, score) != "menu":
        first = "O" if first == "X" else "X"

def preview(x, y, w, h):
    """Mini picture for the launcher tile."""
    s, g = 20, 3
    gx = x + (w - (3 * s + 2 * g)) // 2
    gy = y + (h - (3 * s + 2 * g)) // 2
    marks = {0: "X", 1: "O", 4: "X", 5: "O", 8: "X"}
    for i in range(9):
        cx0, cy0 = gx + (i % 3) * (s + g), gy + (i // 3) * (s + g)
        display.fill_rectangle(cx0, cy0, s, s, C(*CELL_RGB))
        cx, cy = cx0 + s // 2, cy0 + s // 2
        if marks.get(i) == "X":
            stroke(cx - 5, cy - 5, cx + 5, cy + 5, 1, C(*X_RGB))
            stroke(cx + 5, cy - 5, cx - 5, cy + 5, 1, C(*X_RGB))
        elif marks.get(i) == "O":
            display.fill_circle(cx, cy, 7, C(*O_RGB))
            display.fill_circle(cx, cy, 4, C(*CELL_RGB))
    # winning diagonal
    stroke(gx + s // 2, gy + s // 2, gx + 2 * (s + g) + s // 2, gy + 2 * (s + g) + s // 2, 1, YELLOW)
