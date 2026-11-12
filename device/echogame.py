# echogame.py - Echo colour-sequence memory game (launched from main.py)
from hw import (display, font, C, shade, BLACK, WHITE, GREY, BG_TOP_RGB,
                wait_for_tap, wait_release, read_touch_filtered, draw_gradient,
                draw_bevel, text_w, draw_centered_text, end_choice)
import time
import random
import math

NAME = "ECHO"
BEST_FILE = 'echo_best.txt'

YELLOW = C(255, 220, 60)
SHADOW = C(8, 8, 8)

# pad colours: green, red, yellow, blue
PAD_RGB = [(40, 200, 80), (225, 50, 50), (235, 200, 40), (50, 110, 235)]

# --- Layout: 2x2 pads below a 40px header ---
PAD_W, PAD_H = 140, 88
GAP = 8
PAD_X0 = (320 - (2 * PAD_W + GAP)) // 2
PAD_Y0 = 48

def pad_rect(i):
    return PAD_X0 + (i % 2) * (PAD_W + GAP), PAD_Y0 + (i // 2) * (PAD_H + GAP)

def pad_at(px, py):
    for i in range(4):
        x, y = pad_rect(i)
        if x <= px < x + PAD_W and y <= py < y + PAD_H:
            return i
    return None

def wait_pad():
    """Wait for a press on a pad; pad stays lit while held. Returns pad index."""
    while True:
        px, py = wait_for_tap()
        i = pad_at(px, py)
        if i is not None:
            draw_pad(i, lit=True)
            wait_release()
            draw_pad(i, lit=False)
            return i

# --- Drawing ---

def draw_pad(i, lit=False):
    x, y = pad_rect(i)
    rgb = PAD_RGB[i] if lit else shade(PAD_RGB[i], -0.6)
    display.fill_rectangle(x, y, PAD_W, PAD_H, C(*rgb))
    draw_bevel(x, y, PAD_W, PAD_H, rgb, 0.4, -0.5)
    cx, cy = x + PAD_W // 2, y + PAD_H // 2
    if lit:
        # glowing lens in the middle
        display.fill_circle(cx, cy, 24, C(*shade(rgb, 0.35)))
        display.fill_circle(cx, cy, 16, C(*shade(rgb, 0.65)))
        display.fill_circle(cx - 5, cy - 5, 6, WHITE)
    else:
        display.fill_circle(cx, cy, 24, C(*shade(rgb, -0.3)))

def draw_board():
    draw_gradient(0, 0, 320, 240)
    for i in range(4):
        x, y = pad_rect(i)
        display.fill_rectangle(x + 3, y + 3, PAD_W, PAD_H, SHADOW)
        draw_pad(i)

def draw_header(level, best, status, status_color=WHITE):
    display.fill_rectangle(0, 0, 320, 40, BLACK)
    display.draw_text(8, 8, "LV {}".format(level), font, WHITE, BLACK)
    b = "BEST {}".format(best)
    display.draw_text(320 - 8 - text_w(b), 8, b, font, GREY, BLACK)
    display.draw_text((320 - text_w(status)) // 2, 8, status, font, status_color, BLACK)

# --- Best score ---

def load_best():
    try:
        with open(BEST_FILE) as f:
            return int(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0

def save_best(n):
    try:
        with open(BEST_FILE, 'w') as f:
            f.write(str(n))
    except OSError:
        pass

# --- Screens ---

def title_screen(best):
    draw_gradient(0, 0, 320, 240)
    bg = C(*BG_TOP_RGB)
    draw_centered_text(24, "E C H O", WHITE, bg)
    # four mini pads as a logo
    for i, rgb in enumerate(PAD_RGB):
        cx = 160 + (-30 if i % 2 == 0 else 30)
        cy = 100 + (-22 if i < 2 else 22)
        display.fill_rectangle(cx - 26, cy - 18, 52, 36, C(*shade(rgb, -0.4)))
        display.fill_circle(cx, cy, 12, C(*rgb))
        display.fill_circle(cx - 4, cy - 4, 4, WHITE)
    sub = C(*shade(BG_TOP_RGB, 0.9))
    draw_centered_text(158, "WATCH, THEN REPEAT", sub, C(18, 22, 50))
    if best:
        draw_centered_text(188, "BEST: {}".format(best), YELLOW, BLACK)
    draw_centered_text(212, "TAP TO START", GREY, BLACK)
    wait_for_tap()
    wait_release()

def sparkle(cx, cy, colors, frames=4):
    for f in range(frames):
        r = 10 + f * 14
        for a in range(0, 360, 45):
            rad = math.radians(a + f * 20)
            px, py = cx + int(r * math.cos(rad)), cy + int(r * math.sin(rad))
            if 3 <= px < 317 and 43 <= py < 237:
                display.fill_circle(px, py, 2, colors[(a // 45 + f) % len(colors)])
        time.sleep(0.03)

def round_cleared(level):
    draw_header(level, BEST, "NICE!", C(80, 230, 110))
    for i in range(4):
        draw_pad(i, lit=True)
    sparkle(160, 140, [WHITE, YELLOW, C(*PAD_RGB[0])])
    time.sleep(0.15)
    draw_board()

def game_over_screen(score, best, new_best, wrong, right):
    # flash the pad that should have been pressed
    for _ in range(3):
        draw_pad(right, lit=True); time.sleep(0.18)
        draw_pad(right, lit=False); time.sleep(0.12)
    time.sleep(0.3)
    display.clear(BLACK)
    draw_centered_text(40, "GAME OVER", C(230, 60, 60))
    draw_centered_text(85, "SCORE: {}".format(score), WHITE)
    if new_best:
        draw_centered_text(125, "NEW BEST!", YELLOW)
        sparkle(160, 137, [YELLOW, WHITE] + [C(*c) for c in PAD_RGB], frames=6)
        draw_centered_text(125, "NEW BEST!", YELLOW)
    else:
        draw_centered_text(125, "BEST: {}".format(best), GREY)
    return end_choice()

# --- Game ---

BEST = load_best()

def play_sequence(seq, level):
    on = max(0.18, 0.5 - 0.025 * level)
    off = max(0.08, 0.2 - 0.01 * level)
    time.sleep(0.5)
    for i in seq:
        draw_pad(i, lit=True); time.sleep(on)
        draw_pad(i, lit=False); time.sleep(off)

def run_game():
    global BEST
    seq = []
    draw_board()
    while True:
        seq.append(random.randint(0, 3))
        level = len(seq)
        draw_header(level, BEST, "WATCH", YELLOW)
        play_sequence(seq, level)
        draw_header(level, BEST, "GO!", C(80, 230, 110))
        for step, want in enumerate(seq):
            got = wait_pad()
            if got != want:
                score = level - 1
                new_best = score > BEST
                if new_best:
                    BEST = score
                    save_best(BEST)
                return game_over_screen(score, BEST, new_best, got, want)
        round_cleared(level)

# --- Entry points used by main.py ---
def run():
    title_screen(BEST)
    while run_game() != "menu":
        pass

def preview(x, y, w, h):
    """Mini picture of the game for the launcher tile."""
    pw, ph, g = 44, 28, 6
    gx = x + (w - (2 * pw + g)) // 2
    gy = y + (h - (2 * ph + g)) // 2
    for i, rgb in enumerate(PAD_RGB):
        px, py = gx + (i % 2) * (pw + g), gy + (i // 2) * (ph + g)
        lit = (i == 1)
        c = rgb if lit else shade(rgb, -0.55)
        display.fill_rectangle(px, py, pw, ph, C(*c))
        if lit:
            display.fill_circle(px + pw // 2, py + ph // 2, 8, C(*shade(rgb, 0.6)))
            display.fill_circle(px + pw // 2 - 2, py + ph // 2 - 2, 3, WHITE)
