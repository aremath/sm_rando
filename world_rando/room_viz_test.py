from sm_rando.world_rando.room_viz import *
from sm_rando.world_rando.tiles import *

leveldata = {
    (0,0) : Tile(None, Type(0, 0)),
    (0,1) : Tile(None, Type(8, 0)),
    (1,0) : Tile(None, Type(1, 0b01100000)),
    (1,1) : Tile(None, Type(0, 0))
}

room_viz(leveldata, 2, 2, "test.png", "encoding/room_tiles")
