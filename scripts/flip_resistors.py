import pcbnew
board = pcbnew.GetBoard()
for ref in ["R1","R2","R3","R4","R5","R6","R7","R8","R9","R10"]:
    fp = board.FindFootprintByReference(ref)
    if fp and not fp.IsFlipped():
        fp.Flip(fp.GetPosition(), True)
pcbnew.Refresh()
print("Done!")