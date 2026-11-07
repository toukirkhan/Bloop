"""Columns encode pixels from top (bit 0) to bottom (bit 7)."""

FONT = dict(line.split() for line in """
A 7e1111117e
B 7f49494936
C 3e41414122
D 7f4141221c
E 7f49494941
F 7f09090901
G 3e41495172
H 7f0808087f
I 00417f4100
J 2040413f01
K 7f08142241
L 7f40404040
M 7f020c027f
N 7f0408107f
O 3e4141413e
P 7f09090906
Q 3e4151215e
R 7f09192946
S 2649494932
T 01017f0101
U 3f4040403f
V 1f2040201f
W 3f4038403f
X 6314081463
Y 0708700807
Z 6151494543
0 3e5149453e
1 00427f4000
2 4261514946
3 2141454b31
4 1814127f10
5 2745454539
6 3c4a494930
7 0101710907
8 3649494936
9 064949291e
! 5f
? 0201590906
. 60
, 4020
- 080808
' 03
""".splitlines() if line)
FONT[" "] = "000000"

ICONS = {
    "heart": ("💙", ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"]),
    "smile": ("😊", ["0111110", "1000001", "1010101", "1000001", "1011101", "1000001", "0111110"]),
    "star": ("⭐", ["0001000", "0001000", "1111111", "0111110", "0011100", "0110110", "0100010"]),
    "sparkle": ("✨", ["0001000", "0001000", "0011100", "1111111", "0011100", "0001000", "0001000"]),
    "ghost": ("👻", ["0011100", "0111110", "1101011", "1111111", "1110111", "1111111", "1010101"]),
    "flower": ("🌼", ["0010100", "0111110", "0010100", "0111110", "0011100", "1001001", "0111110", "0001000"]),
}

BLANK = bytes(13).hex()


def render(kind, value):
    if kind == "emoji":
        if value not in ICONS:
            raise ValueError("Choose an emoji from the picker.")
        label, rows = ICONS[value]
        width = len(rows[0])
        left = (13 - width) // 2
        top = (8 - len(rows)) // 2
        columns = bytes(sum(int(row[x]) << (y + top) for y, row in enumerate(rows))
                        for x in range(width))
        return label, [(bytes(left) + columns + bytes(13 - width - left)).hex()], 3000

    if kind != "text":
        raise ValueError("Choose text or an emoji.")
    value = value.strip()
    if not 1 <= len(value) <= 40 or not value.isascii():
        raise ValueError("Enter 1–40 English letters, numbers or supported punctuation.")
    glyphs = value.upper()
    if any(char not in FONT for char in glyphs):
        raise ValueError("Supported punctuation is ! ? . , - and apostrophe.")
    strip = bytes(13) + b"".join(bytes.fromhex(FONT[char]) + b"\0" for char in glyphs) + bytes(13)
    return value, [strip[i:i + 13].hex() for i in range(len(strip) - 12)], 80
