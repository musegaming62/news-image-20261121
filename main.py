#!/usr/bin/env python3
"""News poster for Saturday 21 November 2026.

Draws a 1024x1024 newspaper-style front page with pure Python stdlib:
a raster canvas, an embedded 5x7 bitmap font, vector scenes that carry
each story's data, a UTC timeline, a world map with numbered pins, a
dense brief list, and a date-check box naming what was left out.

Deterministic: no randomness, no clock, no network. Running it twice
writes byte-identical PNG files.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 227)
INK = (26, 26, 26)
WHITE = (255, 253, 246)
NAVY = (20, 38, 63)
RED = (179, 39, 30)
BLUE = (23, 78, 122)
TEAL = (15, 107, 92)
GOLD = (176, 124, 0)
GREEN = (46, 107, 46)
ORANGE = (192, 90, 0)
PURPLE = (91, 58, 142)
GREY = (120, 112, 96)
LINE = (216, 208, 188)
LIGHT = (238, 232, 214)
SKY = (205, 224, 238)
SEA = (168, 198, 222)

TAG_COLOR = {"CONFIRMED": GREEN, "REPORTED": BLUE, "CLAIM": RED}

# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 bits, written as strings for readability.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10001", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "10001", "11110", "10000"),
    "q": ("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11110", "01000", "01000", "01001", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ";": ("00000", "00000", "01100", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "#": ("01010", "01010", "11111", "01010", "01010", "11111", "01010"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "~": ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def wrap_text(s, max_width, scale):
    """Greedy word wrap; returns list of lines fitting max_width px."""
    max_chars = max(1, (max_width + scale) // (6 * scale))
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= max_chars:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        r, g, b = color
        row = bytes((r, g, b)) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect(self, x, y, w, h, color, lw=1):
        self.fill(x, y, w, lw, color)
        self.fill(x, y + h - lw, w, lw, color)
        self.fill(x, y, lw, h, color)
        self.fill(x + w - lw, y, lw, h, color)

    def hline(self, x, y, w, color):
        self.fill(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.fill(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=True):
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            if fill:
                self.fill(cx - half, cy + dy, 2 * half + 1, 1, color)
            else:
                self.set(cx - half, cy + dy, color)
                self.set(cx + half, cy + dy, color)

    def poly(self, pts, color):
        """Scanline fill of a simple polygon (list of (x, y))."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    if y1 != y0:
                        xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.fill(int(xs[k]), y, max(1, int(xs[k + 1]) - int(xs[k])), 1, color)

    def text(self, s, x, y, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT["?"])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_center(self, s, cx, y, scale, color):
        self.text(s, cx - text_width(s, scale) // 2, y, scale, color)


# ---------------------------------------------------------------- PNG writer
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", canvas.w, canvas.h,
                                        8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- the news
# Every story verified to an event or first report on Saturday 21 Nov 2026.
# tag: CONFIRMED = independently verified fact; REPORTED = single source;
#      CLAIM = another party's assertion.

# heroes: (number, region tag, headline, dek, tag, source, scene, data)
HEROES = [
    (1, "GULF / CONFLICT",
     "IRAN STRIKES US BASES IN BAHRAIN",
     "IRGC says it hit 2 US positions; Bahrain reports an industrial fire, no injuries; US denies an F-16 was hit.",
     "CONFIRMED", "Al Jazeera", "bahrain", "2 BASES HIT"),
    (2, "MEXICO / JUSTICE",
     "MEXICO CAPTURES 'EL CHAPO ISIDRO'",
     "FBI most-wanted cartel boss seized in a Sinaloa raid; gunfights, fires and roadblocks follow. 11 dead.",
     "CONFIRMED", "BBC", "chapo", "11 DEAD"),
    (3, "ANTALYA / CLIMATE",
     "COP31 CLOSE TO A FINAL DEAL",
     "Talks run past deadline; nearly 200 nations split on fossil fuels, finance and warming targets.",
     "REPORTED", "Reuters", "cop", "200 NATIONS"),
]

# cards: (number, region tag, headline, data line, tag, source, scene, big)
CARDS = [
    (4, "UKRAINE / CONFLICT", "RUSSIAN MISSILE KILLS BOY, 7, IN KRYVYI RIH",
     "2 killed, 58-60 hurt", "CONFIRMED",
     "CNN", "kryvyi", "2 KILLED"),
    (5, "BALTIC / CONFLICT", "DRONES SET RUSSIAN SHIP ABLAZE",
     "Drifts into Finnish waters", "CONFIRMED",
     "Reuters", "ship", "2 DRONES"),
    (6, "MARKETS / ECONOMY", "AI SELL-OFF: NASDAQ ERASES 2026 GAINS",
     "S&P -3.7%, Nikkei -5.06%", "CONFIRMED",
     "BBC", "chart", "-3.7% S&P"),
    (7, "CHINA / POLITICS", "TRUMP DEFENDS PUTIN TIES AT SUMMIT",
     "Nuclear-risk talks agreed", "REPORTED",
     "BBC", "summit", "3-WAY"),
    (8, "SCIENCE / MATHS", "CLAIM: AI HELPED PROVE RIEMANN",
     "Proof claimed in 6 weeks",
     "CLAIM", "Guardian", "riemann", "167 YEARS"),
    (9, "THE HAGUE / JUSTICE", "ICJ: MYANMAR GUILTY OF GENOCIDE",
     "700,000+ fled in 2017",
     "CONFIRMED", "PBS", "scales", "700,000 FLED"),
    (10, "BRAZIL / HEALTH", "MOSQUITOES CUT DENGUE 69% IN BRAZIL",
     "Trial areas shield children",
     "REPORTED", "AP", "mosquito", "-69%"),
    (11, "GAZA / CONFLICT", "ISRAELI STRIKE KILLS 3 IN GAZA VAN",
     "Food van hit in Tel al-Hawa",
     "CONFIRMED", "Al Jazeera", "truck", "3 KILLED"),
    (12, "LONDON / SPORT", "ENGLAND 37-12 ALL BLACKS: RECORD WIN",
     "Biggest margin over NZ",
     "CONFIRMED", "BBC Sport", "rugby", "37-12"),
    (13, "YEMEN / CONFLICT", "HOUTHI-SAUDI STRIKES: 71 IN 24 HOURS",
     "Riyadh missiles intercepted",
     "REPORTED", "Middle East Eye", "missiles", "71 STRIKES"),
    (14, "BRUSSELS / POLITICS", "UK AND EU SIGN THREE POST-BREXIT DEALS",
     "Food, emissions, youth scheme",
     "CONFIRMED", "Guardian", "docs", "3 DEALS"),
    (15, "BRAZIL / POLITICS", "BOLSONARO IN INTENSIVE CARE",
     "Stable, breathing on his own",
     "CONFIRMED", "Al Jazeera", "hospital", "ICU"),
]

# brief list: (number, one-line headline, source, tag)
BRIEF = [
    (16, "FBI crime database hacked", "BBC", "REPORTED"),
    (17, "Trump threatens data-centre tax", "BBC", "REPORTED"),
    (18, "Proxy voting unconstitutional, 9-8", "AP", "CONFIRMED"),
    (19, "Trump posts 'Great Powers 1945, 2026'", "Yonhap", "CONFIRMED"),
    (20, "Denmark expels Russian attache", "BBC", "REPORTED"),
    (21, "UN keeps working on AI weapons rules", "CBC", "REPORTED"),
    (22, "France protests: 144 arrested", "France 24", "REPORTED"),
    (23, "Police sentenced over Zecler beating", "BBC", "CONFIRMED"),
    (24, "Palisades fire arsonist convicted", "BBC", "CONFIRMED"),
    (25, "US child dies of measles in Virginia", "Guardian", "REPORTED"),
    (26, "Pill shows progress vs pancreatic cancer", "BBC", "REPORTED"),
    (27, "Salvadoran troops fight gangs in Haiti", "Guardian", "REPORTED"),
    (28, "Nigeria boat capsizes; 24 dead", "Sky News", "CONFIRMED"),
    (29, "Saudi-Japan oil stockpile deal", "Japan Today", "CONFIRMED"),
    (30, "Brent ~$91 as Gulf attacks meet glut", "OilPrice", "REPORTED"),
    (31, "Argentina bonds fall into distress", "BA Times", "REPORTED"),
    (32, "Man jailed 19y over Sikh murder plot", "BBC", "CONFIRMED"),
    (33, "Turkey takes control of Sozcu TV", "RFI", "REPORTED"),
    (34, "Tanzania opposition leader convicted", "BBC", "CONFIRMED"),
    (35, "Uganda restricts gatherings over Ebola", "Guardian", "REPORTED"),
    (36, "Nvidia chief ousted; Trump talked to Xi", "CNBC", "REPORTED"),
    (37, "Fighting widens in eastern DR Congo", "Asharq", "REPORTED"),
    (38, "Japan sidelined at China summit", "Japan Times", "REPORTED"),
    (39, "EU-Indonesia trade deal signed", "DW", "CONFIRMED"),
    (40, "EU proposes 3% Big Tech tax", "RFI", "REPORTED"),
    (41, "Estonia to shut Russia crossings Dec 1", "ST", "CONFIRMED"),
    (42, "Seoul moves to impeach chief justice", "Yonhap", "REPORTED"),
    (43, "CERN finds ultra-rare decay evidence", "Phys.org", "REPORTED"),
    (44, "Mamdani to close Rikers by 2032", "BBC", "CONFIRMED"),
    (45, "M6.7 quake Peru; M6.8 off Timor", "UPI", "CONFIRMED"),
    (46, "Alcaraz reaches ATP final", "BBC Sport", "CONFIRMED"),
    (47, "Harden 51 pts, passes Kobe", "Guardian", "CONFIRMED"),
    (48, "Australia win 1st T20I at MCG", "BBC Sport", "CONFIRMED"),
    (49, "Verstappen takes Vegas GP pole", "BBC Sport", "CONFIRMED"),
    (50, "Georgia beat USA 38-10", "Sports360", "CONFIRMED"),
]

# UTC timeline: (label, time text) - times as reported; ~ = approximate
TIMELINE = [
    ("~07:00", "Sparta II drone hit"),
    ("09:00", "Tonga v Hong Kong"),
    ("12:30", "Man City 1-1 Fulham"),
    ("14:00", "Georgia v USA"),
    ("14:30", "MI Emirates win"),
    ("Evening", "COP31 near deal"),
    ("Evening", "Iran hits Bahrain"),
]

# Date check: stories deliberately left out, with their real dates.
LEFT_OUT = [
    "GTA VI $3.8bn first day - first day was Nov 18",
    "BepiColombo Mercury orbit - insertion Nov 19-20",
    "Pilotless air taxi flight, Japan - demo Nov 20",
    "Vatican Christmas tree raised - Nov 20",
    "Curiosity Mars cloud photo - taken Oct 31",
]
DUE = [
    "ATP final: Alcaraz v Zverev - Sun Nov 22",
    "Las Vegas GP - Sun Nov 22",
    "Nepal PM visits India - Nov 22-23",
    "Spain election - Nov 29",
]

# ---------------------------------------------------------------- world map
# Coarse continent outlines as (lon, lat) points; equirectangular.
CONTINENTS = [
    [(-168, 66), (-165, 60), (-158, 58), (-152, 60), (-140, 60), (-135, 57),
     (-130, 54), (-125, 49), (-124, 42), (-120, 34), (-114, 29), (-110, 24),
     (-105, 20), (-97, 16), (-94, 17), (-90, 14), (-86, 12), (-83, 9),
     (-80, 8), (-77, 7), (-79, 9), (-82, 10), (-84, 12), (-87, 14),
     (-88, 16), (-91, 19), (-97, 26), (-93, 30), (-89, 30), (-84, 30),
     (-81, 25), (-80, 32), (-76, 35), (-74, 40), (-70, 42), (-68, 45),
     (-65, 44), (-60, 47), (-55, 47), (-60, 50), (-65, 50), (-60, 52),
     (-55, 52), (-60, 55), (-65, 58), (-68, 55), (-70, 58), (-75, 62),
     (-80, 66), (-85, 66), (-90, 66), (-95, 69), (-110, 68), (-125, 70),
     (-140, 70), (-155, 71), (-165, 68), (-168, 66)],
    [(-80, 8), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
     (-70, -23), (-70, -30), (-72, -37), (-73, -44), (-74, -50), (-70, -54),
     (-66, -55), (-68, -50), (-65, -45), (-62, -40), (-58, -35), (-52, -32),
     (-48, -28), (-41, -23), (-39, -17), (-35, -8), (-35, -5), (-40, -3),
     (-44, -2), (-50, 0), (-52, 5), (-55, 6), (-58, 8), (-62, 9),
     (-68, 11), (-72, 12), (-75, 10), (-77, 8), (-80, 8)],
    [(-6, 35), (-10, 31), (-15, 27), (-17, 21), (-17, 15), (-15, 11),
     (-13, 8), (-8, 5), (-4, 5), (0, 6), (6, 4), (9, 4), (9, 0), (12, -5),
     (13, -12), (12, -18), (14, -22), (16, -28), (19, -34), (26, -34),
     (32, -29), (35, -24), (40, -16), (40, -10), (42, -4), (46, -1),
     (51, 2), (51, 11), (48, 11), (44, 11), (40, 15), (38, 18), (35, 20),
     (33, 27), (32, 31), (30, 31), (22, 33), (15, 32), (10, 34), (11, 34),
     (6, 35)],
    [(-10, 36), (-9, 38), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (-1, 49),
     (0, 51), (2, 51), (4, 53), (7, 54), (8, 57), (10, 59), (5, 60),
     (5, 62), (12, 64), (18, 69), (25, 71), (30, 70), (32, 68), (35, 66),
     (40, 66), (44, 68), (50, 68), (55, 68), (60, 69), (68, 69), (68, 66),
     (60, 64), (55, 60), (50, 55), (45, 52), (40, 50), (35, 48), (30, 46),
     (28, 44), (28, 41), (23, 40), (22, 37), (19, 40), (15, 38), (16, 40),
     (12, 42), (8, 44), (3, 43), (-1, 38), (-6, 36), (-10, 36)],
    [(28, 36), (30, 41), (35, 42), (40, 44), (45, 42), (48, 39), (52, 37),
     (56, 38), (60, 40), (63, 42), (60, 45), (58, 48), (55, 51), (50, 54),
     (45, 57), (40, 60), (35, 63), (30, 66), (28, 68), (32, 70), (38, 70),
     (45, 70), (55, 70), (65, 70), (75, 72), (80, 73), (90, 75), (100, 76),
     (110, 76), (120, 75), (130, 72), (140, 72), (150, 70), (160, 69),
     (170, 67), (178, 66), (178, 64), (170, 60), (162, 58), (158, 52),
     (150, 59), (142, 55), (140, 50), (138, 45), (135, 42), (130, 38),
     (127, 35), (122, 38), (120, 32), (118, 28), (112, 22), (108, 18),
     (105, 10), (103, 8), (100, 6), (98, 10), (95, 15), (92, 20),
     (90, 22), (88, 22), (85, 19), (82, 17), (80, 13), (77, 8), (75, 12),
     (72, 20), (68, 22), (66, 25), (62, 25), (58, 26), (56, 27), (54, 26),
     (52, 26), (50, 29), (48, 30), (48, 29), (50, 26), (52, 25), (54, 24),
     (56, 24), (58, 22), (59, 22), (57, 20), (55, 18), (52, 16), (50, 14),
     (48, 14), (45, 13), (43, 12), (40, 15), (39, 20), (38, 25), (35, 28),
     (34, 29), (36, 36), (33, 36), (30, 36)],
    [(113, -22), (114, -30), (115, -33), (118, -35), (124, -33), (129, -32),
     (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -22), (146, -19), (142, -15), (142, -11),
     (137, -12), (135, -15), (132, -12), (130, -13), (126, -14), (122, -17),
     (118, -20), (113, -22)],
    [(130, 31), (132, 33), (134, 34), (137, 35), (139, 37), (141, 39),
     (141, 41), (140, 43), (142, 45), (144, 44), (141, 42), (139, 38),
     (136, 36), (133, 34), (130, 31)],
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51),
     (-1, 50), (-5, 50)],
]

# map pins: story number -> (lon, lat)
PINS = {
    1: (50.6, 26.2), 2: (-107.4, 25.6), 3: (30.7, 36.9), 4: (33.4, 47.9),
    5: (27.0, 59.8), 6: (-74.0, 40.7), 7: (114.1, 22.5), 8: (-122.4, 37.8),
    9: (4.3, 52.1), 10: (-46.6, -23.5), 11: (34.5, 31.5), 12: (-0.1, 51.5),
    13: (42.9, 14.8), 14: (4.35, 50.85), 15: (-47.9, -15.8),
}


import math

# ---------------------------------------------------------------- text (compact)
def draw_compact(cv, s, x, y, color):
    """Scale-1 text with 5px advance (tight, for the brief list)."""
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT["?"])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    cv.set(cx + col, y + row, color)
        cx += 5
    return cx


def badge(cv, cx, cy, num):
    cv.circle(cx, cy, 8, WHITE, fill=True)
    cv.circle(cx, cy, 7, RED, fill=True)
    s = str(num)
    cv.text(s, cx - text_width(s, 1) // 2, cy - 3, 1, WHITE)


# ---------------------------------------------------------------- scenes
# Each draws a small data-carrying scene inside (x, y, w, h).
def scene_draw(cv, kind, x, y, w, h):
    if kind == "bahrain":
        cv.fill(x, y, w, h, (28, 58, 92))
        cv.fill(x, y + h - 6, w, 6, (196, 164, 110))
        for fx in (x + w // 4, x + w // 2 + 8):
            cv.poly([(fx, y + 4), (fx - 7, y + h - 8), (fx + 7, y + h - 8)],
                    (255, 120, 40))
            cv.poly([(fx, y + 10), (fx - 4, y + h - 10), (fx + 4, y + h - 10)],
                    (255, 210, 60))
        cv.fill(x + 6, y + h - 14, 10, 8, WHITE)
        cv.fill(x + w - 16, y + h - 14, 10, 8, WHITE)
    elif kind == "chapo":
        cv.fill(x, y, w, h, WHITE)
        bw = w - 12
        b4 = bw * 4 // 11
        by = y + h // 2 - 6
        cv.fill(x + 6, by, b4, 12, BLUE)
        cv.fill(x + 6 + b4, by, bw - b4, 12, RED)
        cv.text("4", x + 6 + b4 // 2 - 3, by + 3, 1, WHITE)
        cv.text("7", x + 6 + b4 + (bw - b4) // 2 - 3, by + 3, 1, WHITE)
    elif kind == "cop":
        cv.fill(x, y, w, h, (224, 238, 228))
        cx, cy, r = x + w // 2, y + h - 4, min(w // 2 - 4, h - 8)
        for a in range(180, -1, -6):
            px = cx + int(r * math.cos(math.radians(a)))
            py = cy - int(r * math.sin(math.radians(a)))
            cv.set(px, py, TEAL)
            cv.set(px + 1, py, TEAL)
        na = math.radians(36)
        cv.line(cx, cy, cx + int(r * 0.85 * math.cos(na)),
                cy - int(r * 0.85 * math.sin(na)), RED)
        cv.circle(cx, cy, 3, INK, fill=True)
    elif kind == "kryvyi":
        cv.fill(x, y, w, h, WHITE)
        b1 = max(8, (w - 40) * 2 // 62)
        b2 = (w - 40) * 60 // 62
        cv.fill(x + 6, y + 5, b1, 9, RED)
        cv.fill(x + 6, y + h - 14, b2, 9, ORANGE)
        cv.text("2", x + 10 + b1, y + 6, 1, RED)
        cv.text("58-60", x + 10 + b2, y + h - 13, 1, ORANGE)
    elif kind == "ship":
        cv.fill(x, y, w, h, SEA)
        cv.fill(x, y + h - 8, w, 8, (40, 90, 140))
        hx, hy = x + w // 4, y + h // 2
        cv.poly([(hx, hy + 10), (hx + w // 2, hy + 10), (hx + w // 2 - 8, hy - 2),
                 (hx + 8, hy - 2)], (40, 40, 40))
        for i, cc in enumerate((RED, GOLD, TEAL)):
            cv.fill(hx + 12 + i * 14, hy - 12, 12, 10, cc)
        fx = hx + w // 2 - 14
        cv.poly([(fx, hy - 22), (fx - 6, hy - 10), (fx + 6, hy - 10)],
                (255, 120, 40))
    elif kind == "chart":
        cv.fill(x, y, w, h, WHITE)
        cv.vline(x + 8, y + 4, h - 8, GREY)
        cv.hline(x + 8, y + h - 4, w - 12, GREY)
        pts = [(x + 10, y + 6), (x + w // 3, y + h // 3),
               (x + w // 2, y + h // 2), (x + 2 * w // 3, y + 3 * h // 4),
               (x + w - 6, y + h - 8)]
        for i in range(len(pts) - 1):
            cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED)
            cv.line(pts[i][0], pts[i][1] + 1, pts[i + 1][0], pts[i + 1][1] + 1,
                    RED)
        for px, py in pts:
            cv.circle(px, py, 2, RED, fill=True)
    elif kind == "summit":
        cv.fill(x, y, w, h, WHITE)
        bw = (w - 16) // 3
        for i, cc in enumerate((BLUE, RED, GOLD)):
            bx = x + 8 + i * bw
            cv.fill(bx, y + 6, bw - 4, h - 12, cc)
        cv.hline(x + 4, y + h - 4, w - 8, INK)
    elif kind == "riemann":
        cv.fill(x, y, w, h, WHITE)
        for i, px in enumerate((6, 16, 30, 48, 72, 96)):
            if x + px > x + w - 6:
                break
            py = y + h - 8 - (i * (h - 14) // 6)
            cv.circle(x + px, py, 3, PURPLE, fill=True)
        cv.line(x + 6, y + h - 8, x + w - 8, y + 6, PURPLE)
    elif kind == "scales":
        cv.fill(x, y, w, h, WHITE)
        cx = x + w // 2
        cv.vline(cx, y + 4, h - 10, INK)
        cv.hline(cx - w // 3, y + 8, 2 * w // 3, INK)
        for sx in (cx - w // 3, cx + w // 3):
            cv.line(sx, y + 8, sx - 8, y + h - 12, INK)
            cv.line(sx, y + 8, sx + 8, y + h - 12, INK)
            cv.hline(sx - 8, y + h - 12, 17, GOLD)
        cv.fill(cx - 6, y + h - 6, 13, 4, INK)
    elif kind == "mosquito":
        cv.fill(x, y, w, h, (232, 244, 232))
        cx, cy = x + w // 2, y + h // 2
        cv.circle(cx - 8, cy - 8, 7, (200, 220, 235), fill=True)
        cv.circle(cx + 8, cy - 8, 7, (200, 220, 235), fill=True)
        cv.circle(cx, cy, 5, INK, fill=True)
        cv.line(cx + 5, cy - 2, cx + 14, cy - 8, INK)
        cv.line(cx - 5, cy + 3, cx - 13, cy + 8, INK)
        cv.line(cx + 2, cy + 5, cx + 6, cy + 10, INK)
    elif kind == "truck":
        cv.fill(x, y, w, h, WHITE)
        cv.fill(x + 6, y + h // 2 - 4, w // 2, 12, TEAL)
        cv.fill(x + 6 + w // 2, y + h // 2, 12, 8, TEAL)
        cv.circle(x + 14, y + h - 8, 4, INK, fill=True)
        cv.circle(x + w // 2, y + h - 8, 4, INK, fill=True)
        cv.fill(x + w - 22, y + 4, 12, 3, RED)
        cv.fill(x + w - 18, y, 3, 12, RED)
    elif kind == "rugby":
        cv.fill(x, y, w, h, (232, 238, 226))
        cx, cy = x + w // 3, y + h // 2
        for dy in range(-8, 9):
            half = int(14 * (1 - (dy / 9.0) ** 2) ** 0.5)
            cv.fill(cx - half, cy + dy, 2 * half + 1, 1, (122, 72, 32))
        cv.fill(cx - 2, cy - 8, 4, 17, WHITE)
        px = x + 3 * w // 4
        cv.vline(px, y + 4, h - 8, GOLD)
        cv.vline(px + 16, y + 4, h - 8, GOLD)
        cv.hline(px, y + h // 2, 17, GOLD)
    elif kind == "missiles":
        cv.fill(x, y, w, h, (238, 228, 220))
        cv.line(x + 6, y + h - 6, x + w // 2, y + 6, RED)
        cv.line(x + w - 6, y + h - 6, x + w // 2 + 6, y + 10, ORANGE)
        mx, my = x + w // 2, y + h // 3
        for dx, dy in ((-6, -6), (6, -6), (-8, 0), (8, 0), (-6, 6), (6, 6)):
            cv.line(mx, my, mx + dx, my + dy, GOLD)
    elif kind == "docs":
        cv.fill(x, y, w, h, WHITE)
        for i, ox in enumerate((0, 8, 16)):
            cv.fill(x + 6 + ox, y + 4, w // 3, h - 8, LIGHT)
            cv.rect(x + 6 + ox, y + 4, w // 3, h - 8, GREY)
            for r in range(3):
                cv.hline(x + 10 + ox, y + 9 + r * 6, w // 3 - 8, GREY)
        cv.circle(x + w - 12, y + h - 10, 5, RED, fill=True)
    elif kind == "hospital":
        cv.fill(x, y, w, h, WHITE)
        cx, cy = x + w // 2, y + h // 2
        cv.circle(cx, cy, min(w, h) // 2 - 2, (232, 232, 232), fill=True)
        cv.fill(cx - 4, cy - 12, 8, 24, RED)
        cv.fill(cx - 12, cy - 4, 24, 8, RED)


SCENE_DARK = {"bahrain"}


def big_color(kind):
    return WHITE if kind in SCENE_DARK else INK


# ---------------------------------------------------------------- sections
def draw_hero(cv, x, y, w, h, item):
    num, region, headline, dek, tag, src, scene, big = item
    cv.fill(x, y, w, h, WHITE)
    cv.rect(x, y, w, h, LINE)
    badge(cv, x + 12, y + 12, num)
    cv.text(region, x + 28, y + 9, 1, GREY)
    sx, sy, sw, sh = x + 6, y + 26, w - 12, 74
    scene_draw(cv, scene, sx, sy, sw, sh - 18)
    cv.fill(sx, sy + sh - 18, sw, 18, INK)
    cv.text_center(big, sx + sw // 2, sy + sh - 17, 1, WHITE)
    yy = y + 26 + sh + 6
    for ln in wrap_text(headline, w - 16, 2)[:2]:
        cv.text(ln, x + 8, yy, 2, INK)
        yy += 15
    for ln in wrap_text(dek, w - 16, 1)[:3]:
        cv.text(ln, x + 8, yy, 1, (60, 58, 50))
        yy += 9
    cv.text(tag, x + 8, y + h - 14, 1, TAG_COLOR[tag])
    cv.text(" - " + src, x + 8 + text_width(tag, 1), y + h - 14, 1, GREY)


def draw_card(cv, x, y, w, h, item):
    num, region, headline, data, tag, src, scene, big = item
    cv.fill(x, y, w, h, WHITE)
    cv.rect(x, y, w, h, LINE)
    badge(cv, x + 10, y + 11, num)
    cv.text(region, x + 24, y + 8, 1, GREY)
    sx, sy, sw, sh = x + 5, y + 17, w - 10, 30
    cv.fill(sx, sy, sw, sh, LIGHT)
    scene_draw(cv, scene, sx + 2, sy + 2, sw - 158, sh - 4)
    bw = text_width(big, 2)
    cv.text(big, sx + sw - 6 - bw, sy + 8, 2, big_color(scene))
    yy = y + 50
    for ln in wrap_text(headline, w - 12, 2)[:2]:
        cv.text(ln, x + 6, yy, 2, INK)
        yy += 14
    ty = y + h - 12
    tx = x + 6
    tx = draw_compact(cv, data + " - ", tx, ty, (60, 58, 50))
    tx = draw_compact(cv, tag + " ", tx, ty, TAG_COLOR[tag])
    draw_compact(cv, src, tx, ty, GREY)


def draw_map(cv, x, y, w, h):
    cv.fill(x, y, w, h, SEA)
    cv.rect(x, y, w, h, LINE)
    for cont in CONTINENTS:
        pts = [(int(x + (lon + 168) / 348 * w),
                int(y + (80 - lat) / 135 * h)) for lon, lat in cont]
        cv.poly(pts, (186, 203, 176))
    shift = {5: (-14, -8), 11: (14, -12), 12: (-16, -8), 13: (-16, 10),
             14: (16, 12), 15: (16, -8)}
    for num, (lon, lat) in sorted(PINS.items()):
        px = int(x + (lon + 168) / 348 * w)
        py = int(y + (80 - lat) / 135 * h)
        dx, dy = shift.get(num, (0, 0))
        if (dx, dy) != (0, 0):
            cv.line(px, py, px + dx, py + dy, INK)
            px, py = px + dx, py + dy
        cv.circle(px, py, 9, WHITE, fill=True)
        cv.circle(px, py, 8, RED, fill=True)
        s = str(num)
        cv.text(s, px - text_width(s, 1) // 2, py - 3, 1, WHITE)


def render():
    cv = Canvas(W, H, PAPER)
    total = len(HEROES) + len(CARDS) + len(BRIEF)

    # masthead
    cv.fill(0, 0, W, 76, NAVY)
    cv.text("THE WORLD IN ONE DAY", 14, 10, 3, WHITE)
    date = "SATURDAY 21 NOVEMBER 2026"
    cv.text(date, W - 14 - text_width(date, 2), 12, 2, (255, 210, 90))
    cv.text("50 STORIES - 6 CONTINENTS - 12 FIELDS - EVERY STORY TAGGED AND SOURCED",
            14, 48, 1, (200, 205, 215))
    cv.text("ALL EVENTS OF 21 NOV 2026, VERIFIED BY DATE",
            W - 14 - text_width("ALL EVENTS OF 21 NOV 2026, VERIFIED BY DATE", 1),
            48, 1, (200, 205, 215))

    # heroes
    for i, item in enumerate(HEROES):
        draw_hero(cv, 8 + i * 334, 80, 328, 190, item)

    # UTC timeline
    cv.fill(8, 274, 1008, 34, LIGHT)
    cv.rect(8, 274, 1008, 34, LINE)
    cv.text("UTC", 16, 278, 2, RED)
    cv.text("TIMELINE", 16, 294, 1, INK)
    cell = 126
    for i, (t, label) in enumerate(TIMELINE):
        ex = 8 + cell * (i + 1)
        cv.text(t, ex + 6, 278, 1, RED)
        yy = 288
        for ln in wrap_text(label, cell - 12, 1)[:2]:
            cv.text(ln, ex + 6, yy, 1, INK)
            yy += 8

    # top stories header
    cv.text("TOP STORIES", 8, 314, 2, NAVY)
    cv.text("12 MORE - NUMBERED 4 TO 15, PINNED ON THE MAP BELOW",
            8 + text_width("TOP STORIES", 2) + 12, 318, 1, GREY)
    cv.hline(8, 330, 1008, NAVY)

    # cards grid
    for r in range(4):
        for c in range(3):
            item = CARDS[r * 3 + c]
            draw_card(cv, 8 + c * 334, 332 + r * 96, 328, 96, item)

    # bottom divider
    cv.hline(8, 718, 1008, NAVY)

    # map column
    cv.text("WORLD MAP - WHERE IT HAPPENED", 8, 726, 1, NAVY)
    draw_map(cv, 8, 740, 336, 136)
    cv.text("DATE CHECK - LEFT OUT ON PURPOSE", 8, 884, 1, RED)
    yy = 896
    cv.text("LEFT OUT - wrong date:", 8, yy, 1, INK)
    yy += 10
    for s in LEFT_OUT:
        cv.text("- " + s, 8, yy, 1, (60, 58, 50))
        yy += 9
    cv.text("DUE NEXT:", 8, yy, 1, INK)
    yy += 10
    for s in DUE:
        cv.text("- " + s, 8, yy, 1, (60, 58, 50))
        yy += 9

    # brief list column
    cv.text("THE DAY IN BRIEF - 35 MORE STORIES", 352, 726, 1, NAVY)
    lx = 1016
    for tag, col in (("CLAIM", RED), ("REPORTED", BLUE), ("CONFIRMED", GREEN)):
        t = tag + " "
        lx -= text_width(t, 1)
        cv.text(tag, lx, 726, 1, col)
        lx -= 8
        cv.fill(lx, 727, 6, 6, col)
        lx -= 4
    half = (len(BRIEF) + 1) // 2
    for col_i, chunk in enumerate((BRIEF[:half], BRIEF[half:])):
        cx0 = 352 + col_i * 332
        for j, (num, head, src, tag) in enumerate(chunk):
            ry = 740 + j * 14
            if j % 2 == 0:
                cv.fill(cx0 - 2, ry - 2, 326, 13, LIGHT)
            line = "%d %s - %s %s" % (num, head, src, tag)
            draw_compact(cv, str(num), cx0, ry + 2, TAG_COLOR[tag])
            draw_compact(cv, line[len(str(num)) + 1:], cx0 + 14, ry + 2, INK)

    # footer
    cv.hline(8, 1000, 1008, LINE)
    cv.text("Sources: BBC, Reuters, AP, Al Jazeera, Guardian, CNN, Yonhap, France 24, DW, UPI, CBC, PBS, NPR, Sky News, Phys.org, OilPrice.",
            8, 1004, 1, GREY)
    cv.text("Tags: CONFIRMED = verified fact. REPORTED = single source. CLAIM = another party's assertion. Map pins match story numbers 1-15.",
            8, 1013, 1, GREY)
    return cv


def main():
    cv = render()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(cv, path)
    total = len(HEROES) + len(CARDS) + len(BRIEF)
    print("wrote %s (%d bytes, %d stories)" % (path, size, total))


if __name__ == "__main__":
    main()
