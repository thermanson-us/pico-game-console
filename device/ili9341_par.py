# ili9341_par.py - 8-bit parallel ILI9341 (Uno-shield) + 4-wire resistive touch
# for Raspberry Pi Pico 2 W, MicroPython. Save this file ON THE PICO.
#
# Wiring:  LCD_D0..D7 = GP0..GP7   LCD_WR = GP8   LCD_RD = GP9   LCD_RST = GP10
#          LCD_RS = GP26 (ADC0)    LCD_CS = GP27 (ADC1)   5V = VBUS   GND = GND
# Touch:   XP = LCD_D0 (GP0)  XM = LCD_RS (GP26)  YP = LCD_CS (GP27)  YM = LCD_D1 (GP1)

from machine import Pin, ADC, mem32
import rp2, time, math

D0, WR, RD, RST, RS, CS = 0, 8, 9, 10, 26, 27

def color565(r, g, b):
    return (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3
XP, YM, XM, YP = 0, 1, RS, CS

@rp2.asm_pio(out_init=(rp2.PIO.OUT_LOW,) * 8, sideset_init=rp2.PIO.OUT_HIGH,
             out_shiftdir=rp2.PIO.SHIFT_RIGHT)
def _par8():
    wrap_target()
    pull(block).side(1)      # WR high while idle; rising edge latches previous byte
    out(pins, 8).side(0)
    nop().side(0)
    wrap()

def _to_pio0(g):
    try:
        Pin(g, Pin.ALT, alt=Pin.ALT_PIO0)
    except Exception:
        # fallback: IO_BANK0 GPIOn_CTRL.FUNCSEL = 6 (PIO0 on RP2350)
        a = 0x40028000 + 8 * g + 4
        mem32[a] = (mem32[a] & ~0x1F) | 6

class LCD:
    W, H = 240, 320

    def __init__(self, freq=10_000_000, madctl=0x48, w=240, h=320, sm_id=0):
        # landscape: madctl=0x28 (or 0xE8 if upside down), w=320, h=240
        self.W, self.H = w, h
        Pin(RD, Pin.OUT, value=1)
        self.rs = Pin(RS, Pin.OUT, value=1)
        self.cs = Pin(CS, Pin.OUT, value=1)
        self.rst = Pin(RST, Pin.OUT, value=1)
        self.sm = rp2.StateMachine(sm_id, _par8, freq=freq,
                                   out_base=Pin(D0), sideset_base=Pin(WR))
        self.sm.active(1)
        self.cs(0)
        # fast init: hardware reset (no software reset needed), then clear the
        # frame memory to black BEFORE turning the display on, so whatever junk
        # is in GRAM is never shown.
        self.rst(0); time.sleep_ms(1); self.rst(1); time.sleep_ms(120)
        self.cmd(0x11); time.sleep_ms(5)           # sleep out
        self.cmd(0x3A, b"\x55")                    # 16-bit colour
        self.cmd(0x36, bytes([madctl]))
        self.fill(0)                               # black while still display-off
        self.cmd(0x29)                             # display on

    def idle(self):
        while self.sm.tx_fifo():
            pass
        time.sleep_us(2)

    def cmd(self, c, data=None):
        self.idle(); self.rs(0)
        self.sm.put(c)
        self.idle(); self.rs(1)
        if data:
            self.sm.put(bytearray(data))

    def window(self, x, y, w, h):
        x1, y1 = x + w - 1, y + h - 1
        self.cmd(0x2A, bytes([x >> 8, x & 0xFF, x1 >> 8, x1 & 0xFF]))
        self.cmd(0x2B, bytes([y >> 8, y & 0xFF, y1 >> 8, y1 & 0xFF]))
        self.cmd(0x2C)

    def rect(self, x, y, w, h, color):
        if x < 0: w += x; x = 0
        if y < 0: h += y; y = 0
        w = min(w, self.W - x); h = min(h, self.H - y)
        if w <= 0 or h <= 0:
            return
        self.window(x, y, w, h)
        row = bytearray([color >> 8, color & 0xFF] * w)
        for _ in range(h):
            self.sm.put(row)
        self.idle()

    def fill(self, color):
        self.rect(0, 0, self.W, self.H, color)

    def blit(self, x, y, w, h, buf):
        """buf = big-endian RGB565 bytes, w*h*2 long"""
        self.window(x, y, w, h)
        self.sm.put(buf)
        self.idle()

    # --- drawing API compatible with rdagger's ili9341.Display (what the game uses) ---
    def fill_rectangle(self, x, y, w, h, color):
        self.rect(x, y, w, h, color)

    def clear(self, color=0):
        self.fill(color)

    def draw_rectangle(self, x, y, w, h, color):
        self.rect(x, y, w, 1, color)
        self.rect(x, y + h - 1, w, 1, color)
        self.rect(x, y, 1, h, color)
        self.rect(x + w - 1, y, 1, h, color)

    def fill_circle(self, x0, y0, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.rect(x0 - dx, y0 + dy, 2 * dx + 1, 1, color)

    def fill_polygon(self, sides, x0, y0, r, color, rotate=0):
        th = math.radians(rotate)
        pts = [(r * math.cos(2 * math.pi * s / sides + th) + x0,
                r * math.sin(2 * math.pi * s / sides + th) + y0) for s in range(sides)]
        ymin = int(min(p[1] for p in pts)); ymax = int(max(p[1] for p in pts))
        for y in range(ymin, ymax + 1):
            yc = y + 0.5
            xs = []
            for i in range(sides):
                xa, ya = pts[i]; xb, yb = pts[(i + 1) % sides]
                if (ya <= yc < yb) or (yb <= yc < ya):
                    xs.append(xa + (yc - ya) * (xb - xa) / (yb - ya))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                xl = int(xs[j] + 0.5); xr = int(xs[j + 1] + 0.5)
                if xr >= xl:
                    self.rect(xl, y, xr - xl + 1, 1, color)

    def draw_text(self, x, y, text, font, color, background=0, landscape=False, spacing=1):
        bg = background or 0
        for ch in text:
            buf, w, h = font.get_letter(ch, color, bg)
            if w == 0:
                continue
            if x + w > self.W or y + h > self.H:
                break
            self.blit(x, y, w, h, buf)
            x += w
            if spacing:
                self.rect(x, y, spacing, h, bg)
            x += spacing

    # --- touch shares GP0/GP1/GP26/GP27 with the LCD bus ---
    def release_bus(self):
        self.idle()

    def reclaim_bus(self):
        _to_pio0(XP); _to_pio0(YM)
        self.rs.init(Pin.OUT, value=1)
        self.cs.init(Pin.OUT, value=0)


class Touch:
    ZMIN = 200          # pressure threshold - tune if needed

    def __init__(self, lcd, cal=None):
        self.lcd = lcd
        self.cal = cal  # (swap, ax, bx, ay, by)

    @staticmethod
    def _adc(g, n=9):
        a = ADC(Pin(g))
        s = sorted(a.read_u16() >> 4 for _ in range(n))
        return s[n // 2], s[-2] - s[1]          # median, spread

    def raw(self):
        """(x, y, z) raw 12-bit readings, or None if not touched / unstable"""
        self.lcd.release_bus()
        res = None
        # pressure: XP low, YM high, read XM and YP
        Pin(XP, Pin.OUT, value=0); Pin(YM, Pin.OUT, value=1)
        time.sleep_us(20)
        z1, _ = self._adc(XM); z2, _ = self._adc(YP)
        z = 4095 - (z2 - z1)
        if z > self.ZMIN:
            # X: XP high, XM low, sense YP
            Pin(YM, Pin.IN); Pin(XP, Pin.OUT, value=1); Pin(XM, Pin.OUT, value=0)
            time.sleep_us(20)
            x, sx = self._adc(YP)
            # Y: YP high, YM low, sense XM
            Pin(XP, Pin.IN); Pin(YP, Pin.OUT, value=1); Pin(YM, Pin.OUT, value=0)
            time.sleep_us(20)
            y, sy = self._adc(XM)
            if sx < 120 and sy < 120:
                res = (x, y, z)
        self.lcd.reclaim_bus()
        return res

    def read(self):
        """calibrated screen (x, y) or None"""
        r = self.raw()
        if r is None or self.cal is None:
            return None
        swap, ax, bx, ay, by = self.cal
        rx, ry = (r[1], r[0]) if swap else (r[0], r[1])
        x = int(ax * rx + bx); y = int(ay * ry + by)
        return (max(0, min(self.lcd.W - 1, x)), max(0, min(self.lcd.H - 1, y)))

    def wait_press(self, n=6):
        """block until a firm touch; returns averaged raw (x, y)"""
        while True:
            pts = []
            while len(pts) < n:
                r = self.raw()
                if r is None:
                    break
                pts.append(r)
                time.sleep_ms(5)
            if len(pts) == n:
                return (sum(p[0] for p in pts) // n, sum(p[1] for p in pts) // n)
            time.sleep_ms(10)

    def wait_release(self):
        clear = 0
        while clear < 5:
            clear = clear + 1 if self.raw() is None else 0
            time.sleep_ms(10)
