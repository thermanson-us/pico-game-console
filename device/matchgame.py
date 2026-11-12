# matchgame.py - Memory Match (launched from main.py)
from hw import (display, font, C, shade, BLACK, WHITE, GREY, BG_TOP_RGB,
                wait_for_tap, draw_gradient, draw_bevel, draw_centered_text, end_choice)
import time
import random
import math

NAME = "MATCH"

GREEN = C(0, 200, 0)
ACCENT = C(80, 100, 200)
CARDBACK_RGB = (30, 40, 90)
CARDBACK = C(*CARDBACK_RGB)
FRONT_BASE_RGB = (235, 235, 240)
SHADOW = C(8, 8, 8)

# shape_id -> (kind, sides, rotate, rgb)  kind 0=circle, 1=polygon
SHAPES = [
    (0, 0, 0, (230, 60, 60)),
    (1, 4, 0, (60, 100, 230)),
    (1, 3, 0, (230, 210, 40)),
    (1, 4, 45, (60, 200, 90)),
    (1, 5, 0, (160, 70, 220)),
    (1, 6, 0, (230, 140, 40)),
]

def shuffle(lst):
    for i in range(len(lst) - 1, 0, -1):
        j = random.randint(0, i)
        lst[i], lst[j] = lst[j], lst[i]

# --- Grid setup ---
COLS, ROWS = 4, 3
CARD_W, CARD_H = 65, 55
GAP = 8
GRID_X0, GRID_Y0 = 15, 48

def card_rect(idx):
    row, col = idx // COLS, idx % COLS
    return GRID_X0 + col * (CARD_W + GAP), GRID_Y0 + row * (CARD_H + GAP)

def card_at(px, py):
    for i in range(COLS * ROWS):
        x, y = card_rect(i)
        if x <= px <= x + CARD_W and y <= py <= y + CARD_H:
            return i
    return None

# --- Drawing helpers ---
def draw_sphere_icon(cx, cy, r, rgb):
    display.fill_circle(cx, cy, r, C(*shade(rgb, -0.35)))
    display.fill_circle(cx, cy, int(r * 0.8), C(*rgb))
    display.fill_circle(cx - r // 4, cy - r // 4, int(r * 0.45), C(*shade(rgb, 0.4)))
    display.fill_circle(cx - r // 3, cy - r // 3, max(2, r // 4), C(*shade(rgb, 0.75)))

def draw_icon(cx, cy, r, shape_id):
    kind, sides, rotate, rgb = SHAPES[shape_id]
    if kind == 0:
        draw_sphere_icon(cx, cy, r, rgb)
    else:
        display.fill_polygon(sides, cx, cy, r + 2, C(*shade(rgb, -0.3)), rotate)
        display.fill_polygon(sides, cx, cy, r, C(*rgb), rotate)
        display.fill_circle(cx - r // 3, cy - r // 3, max(2, r // 3), C(*shade(rgb, 0.6)))

def draw_card_back(idx):
    x, y = card_rect(idx)
    display.fill_rectangle(x + 3, y + 3, CARD_W, CARD_H, SHADOW)
    display.fill_rectangle(x, y, CARD_W, CARD_H, CARDBACK)
    draw_bevel(x, y, CARD_W, CARD_H, CARDBACK_RGB, 0.35, -0.45)
    display.fill_polygon(4, x + CARD_W // 2, y + CARD_H // 2, 10, ACCENT, 45)

def draw_card_front(idx, shape_id, matched=False):
    x, y = card_rect(idx)
    display.fill_rectangle(x + 3, y + 3, CARD_W, CARD_H, SHADOW)
    display.fill_rectangle(x, y, CARD_W, CARD_H, C(*FRONT_BASE_RGB))
    draw_bevel(x, y, CARD_W, CARD_H, FRONT_BASE_RGB, 0.5, -0.25)
    display.draw_rectangle(x, y, CARD_W, CARD_H, GREEN if matched else GREY)
    draw_icon(x + CARD_W // 2, y + CARD_H // 2, 18, shape_id)

def _flip(idx, first, second):
    x, y = card_rect(idx)
    cx = x + CARD_W // 2
    for i, s in enumerate([1.0, 0.6, 0.25, 0.6, 1.0]):
        w = max(4, int(CARD_W * s))
        display.fill_rectangle(x, y, CARD_W, CARD_H, BLACK)
        display.fill_rectangle(cx - w // 2, y, w, CARD_H, first if i < 2 else second)
        if s > 0.5:
            time.sleep(0.02)

def flip_card_to_front(idx, shape_id):
    _flip(idx, CARDBACK, C(*FRONT_BASE_RGB))
    draw_card_front(idx, shape_id)

def flip_card_to_back(idx):
    _flip(idx, C(*FRONT_BASE_RGB), CARDBACK)
    draw_card_back(idx)

def match_burst(idx):
    x, y = card_rect(idx)
    cx, cy = x + CARD_W // 2, y + CARD_H // 2
    colors = [GREEN, WHITE, C(255, 230, 80)]
    for radius in (6, 14, 22):
        col = colors[radius % len(colors)]
        for angle in (0, 60, 120, 180, 240, 300):
            rad = math.radians(angle)
            display.fill_circle(cx + int(radius * math.cos(rad)),
                                cy + int(radius * math.sin(rad)), 2, col)
        time.sleep(0.03)

def draw_header(moves, pairs_left):
    display.fill_rectangle(0, 0, 320, 40, BLACK)
    display.draw_text(10, 8, "MOVES: {}".format(moves), font, WHITE, BLACK)
    display.draw_text(190, 8, "LEFT: {}".format(pairs_left), font, WHITE, BLACK)

# --- Screens ---
def title_screen():
    draw_gradient(0, 0, 320, 240)
    bg = C(*BG_TOP_RGB)
    draw_centered_text(30, "MEMORY MATCH", WHITE, bg)
    spacing = 320 // (len(SHAPES) + 1)
    for i in range(len(SHAPES)):
        draw_icon(spacing * (i + 1), 110, 20, i)
    draw_centered_text(180, "TAP TO START", GREY, BLACK)
    wait_for_tap()

def celebration_burst():
    cx, cy = 160, 120
    for frame in range(3):
        for i in range(10):
            rad = math.radians(random.randint(0, 359))
            radius = random.randint(20, 110)
            px, py = cx + int(radius * math.cos(rad)), cy + int(radius * math.sin(rad))
            if 0 <= px < 320 and 0 <= py < 240:
                display.fill_circle(px, py, 3, C(*random.choice(SHAPES)[3]))
        time.sleep(0.05)

def win_screen(moves):
    display.clear(BLACK)
    celebration_burst()
    draw_centered_text(70, "YOU WIN!", GREEN)
    draw_centered_text(110, "MOVES: {}".format(moves), WHITE)
    return end_choice()

# --- Game ---
def run_game():
    shape_ids = list(range(len(SHAPES))) * 2
    shuffle(shape_ids)
    revealed = [False] * 12
    matched = [False] * 12
    moves = 0
    pairs_left = len(SHAPES)

    draw_gradient(0, 0, 320, 240)
    draw_header(moves, pairs_left)
    for i in range(12):
        draw_card_back(i)

    selected = []
    while pairs_left > 0:
        px, py = wait_for_tap()
        idx = card_at(px, py)
        if idx is None or revealed[idx] or matched[idx] or idx in selected:
            continue
        revealed[idx] = True
        flip_card_to_front(idx, shape_ids[idx])
        selected.append(idx)

        if len(selected) == 2:
            moves += 1
            a, b = selected
            if shape_ids[a] == shape_ids[b]:
                matched[a] = matched[b] = True
                draw_card_front(a, shape_ids[a], matched=True)
                draw_card_front(b, shape_ids[b], matched=True)
                match_burst(a)
                match_burst(b)
                draw_card_front(a, shape_ids[a], matched=True)
                draw_card_front(b, shape_ids[b], matched=True)
                pairs_left -= 1
            else:
                time.sleep(0.5)
                revealed[a] = revealed[b] = False
                flip_card_to_back(a)
                flip_card_to_back(b)
            selected = []
            draw_header(moves, pairs_left)
    return moves

# --- Entry points used by main.py ---
def run():
    title_screen()
    while True:
        moves = run_game()
        if win_screen(moves) == "menu":
            return

def preview(x, y, w, h):
    """Mini picture of the game for the launcher tile."""
    cw, ch, g = 26, 18, 4
    gx = x + (w - (4 * cw + 3 * g)) // 2
    gy = y + (h - (3 * ch + 2 * g)) // 2
    faces = {1: 0, 6: 3, 10: 5}            # a few face-up cards
    for i in range(12):
        cx, cy = gx + (i % 4) * (cw + g), gy + (i // 4) * (ch + g)
        if i in faces:
            display.fill_rectangle(cx, cy, cw, ch, C(*FRONT_BASE_RGB))
            kind, sides, rot, rgb = SHAPES[faces[i]]
            if kind == 0:
                display.fill_circle(cx + cw // 2, cy + ch // 2, 6, C(*rgb))
            else:
                display.fill_polygon(sides, cx + cw // 2, cy + ch // 2, 7, C(*rgb), rot)
        else:
            display.fill_rectangle(cx, cy, cw, ch, CARDBACK)
            display.fill_polygon(4, cx + cw // 2, cy + ch // 2, 4, ACCENT, 45)
