# hw.py - shared hardware + UI helpers for the Pico 2 W game console
# Display, touch and font are created ONCE here; every game imports them.

from ili9341_par import LCD, Touch, color565
from xglcd_font import XglcdFont
import time

TOUCH_CAL = (True, -0.09875, 369.8, 0.08253, -42.9)   # from touch_paint.py
W, H = 320, 240

display = LCD(madctl=0x28, w=W, h=H)
touch = Touch(display, cal=TOUCH_CAL)
font = XglcdFont('fonts/Unispace12x24.c', 12, 24)

# ---------------------------------------------------------------- colours
def C(r, g, b):
    return color565(r, g, b)

def shade(rgb, factor):
    r, g, b = rgb
    if factor >= 0:
        return (min(255, int(r + (255 - r) * factor)),
                min(255, int(g + (255 - g) * factor)),
                min(255, int(b + (255 - b) * factor)))
    return (max(0, int(r * (1 + factor))),
            max(0, int(g * (1 + factor))),
            max(0, int(b * (1 + factor))))

BLACK = C(0, 0, 0)
WHITE = C(255, 255, 255)
GREY = C(110, 110, 110)
BG_TOP_RGB = (18, 22, 50)
BG_BOTTOM_RGB = (0, 0, 0)

# ---------------------------------------------------------------- touch
def median(vals):
    s = sorted(vals)
    return s[len(s) // 2]

def read_touch_filtered(samples=3, min_valid=2):
    xs, ys = [], []
    for _ in range(samples):
        p = touch.read()
        if p:
            xs.append(p[0]); ys.append(p[1])
    if len(xs) < min_valid:
        return None
    return median(xs), median(ys)

def wait_release():
    clear = 0
    while clear < 3:
        clear = clear + 1 if read_touch_filtered() is None else 0
        time.sleep(0.01)

def wait_for_tap():
    """Wait for a fresh press (finger must lift first). Returns (x, y)."""
    wait_release()
    while True:
        pos = read_touch_filtered()
        if pos:
            return pos
        time.sleep(0.01)

# ---------------------------------------------------------------- drawing
def draw_gradient(x, y, w, h, top_rgb=BG_TOP_RGB, bottom_rgb=BG_BOTTOM_RGB, bands=24):
    band_h = max(1, h // bands)
    for i in range(bands):
        t = i / (bands - 1)
        c = C(int(top_rgb[0] + (bottom_rgb[0] - top_rgb[0]) * t),
              int(top_rgb[1] + (bottom_rgb[1] - top_rgb[1]) * t),
              int(top_rgb[2] + (bottom_rgb[2] - top_rgb[2]) * t))
        yy = y + i * band_h
        hh = band_h if i < bands - 1 else h - band_h * (bands - 1)
        display.fill_rectangle(x, yy, w, hh, c)

def draw_bevel(x, y, w, h, base_rgb, light_amt, dark_amt, t=3):
    light = C(*shade(base_rgb, light_amt))
    dark = C(*shade(base_rgb, dark_amt))
    display.fill_rectangle(x, y, w, t, light)
    display.fill_rectangle(x, y, t, h, light)
    display.fill_rectangle(x, y + h - t, w, t, dark)
    display.fill_rectangle(x + w - t, y, t, h, dark)

def text_w(text):
    return font.measure_text(text)

def draw_text_centered_in(x, w, y, text, color, bg=BLACK):
    display.draw_text(x + (w - text_w(text)) // 2, y, text, font, color, bg)

def draw_centered_text(y, text, color, bg=BLACK):
    draw_text_centered_in(0, W, y, text, color, bg)

# ---------------------------------------------------------------- buttons
def draw_button(x, y, w, h, text, rgb):
    display.fill_rectangle(x + 3, y + 3, w, h, C(8, 8, 8))
    display.fill_rectangle(x, y, w, h, C(*rgb))
    draw_bevel(x, y, w, h, rgb, 0.4, -0.5)
    draw_text_centered_in(x, w, y + (h - 24) // 2, text, WHITE, C(*rgb))

def end_choice(y=184):
    """Draw PLAY AGAIN / MENU buttons and wait. Returns 'again' or 'menu'."""
    again = (22, y, 156, 40)
    menu = (198, y, 100, 40)
    draw_button(*again, "PLAY AGAIN", (40, 140, 70))
    draw_button(*menu, "MENU", (70, 80, 150))
    while True:
        px, py = wait_for_tap()
        for name, (x, yy, w, h) in (("again", again), ("menu", menu)):
            if x <= px < x + w and yy <= py < yy + h:
                wait_release()
                return name
