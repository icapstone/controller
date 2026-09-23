import pcbnew, math
board = pcbnew.GetBoard()
cx, cy = 150790000, 77000000
led_r = 11000000  # move from 9.5mm to 11mm, away from inner hole

pairs = [
    ("D1", "R1", 0), ("D6", "R6", 36), ("D2", "R2", 72),
    ("D7", "R7", 108), ("D3", "R3", 144), ("D8", "R8", 180),
    ("D4", "R4", 216), ("D9", "R9", 252), ("D5", "R5", 288),
    ("D10", "R10", 324),
]

for led_ref, res_ref, angle_deg in pairs:
    angle_rad = math.radians(angle_deg)
    x = cx + int(led_r * math.cos(angle_rad))
    y = cy + int(led_r * math.sin(angle_rad))
    fp = board.FindFootprintByReference(led_ref)
    if fp:
        fp.SetPosition(pcbnew.VECTOR2I(x, y))

pcbnew.Refresh()
print("Done!")