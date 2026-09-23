import pcbnew, math
board = pcbnew.GetBoard()
cx, cy = 150790000, 77000000
led_r = 9500000  # bump from 9mm to 9.5mm
for i, ref in enumerate(["D1","D6","D2","D7","D3","D8","D4","D9","D5","D10"]):
    angle_rad = math.radians(i * 36)
    fp = board.FindFootprintByReference(ref)
    if fp:
        fp.SetPosition(pcbnew.VECTOR2I(cx + int(led_r * math.cos(angle_rad)), cy + int(led_r * math.sin(angle_rad))))
pcbnew.Refresh()