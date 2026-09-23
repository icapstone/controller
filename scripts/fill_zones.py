import pcbnew
board = pcbnew.GetBoard()
for zone in board.Zones():
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.Refresh()
print("Done!")