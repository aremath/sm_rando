import sys
import clingo
import random
from itertools import product
# Relies on Isaac Karth's wfc implementation: https://github.com/ikarth/wfc_2019f
# This only works from the top level directory...
sys.path.append("../wfc_2019f")
from wfc import wfc_patterns, wfc_tiles, wfc_adjacency
from rom_tools.rom_data_structures import LevelData
from rom_tools.leveldata_utils import *
from world_rando.coord import Coord, Rect
from world_rando.room_gen import wfc_rectangularize

def get_cross(p):
    """ Cross-shaped group of coords centered on p """
    directions = [Coord(0,0), Coord(1,0), Coord(-1,0), Coord(0,1), Coord(0,-1)]
    return [p + d for d in directions]

def get_fixed_tiles(room_header):
    """Compute the set of tiles that should be fixed for WFC for a given room header"""
    fixed_tiles = set()
    screen_map = set()
    all_states = room_header.all_states()
    #all_states = [s.state for s in room_header.state_chooser.conditions] + [room_header.state_chooser.default]
    shapes = [state.level_data.level_array.layer1.shape for state in all_states]
    # Hopefully all level datas have the same shape...
    assert len(set(shapes)) == 1
    for state in all_states:
        # Add doors
        layer1 = state.level_data.level_array.layer1
        def inbounds(c):
            if c[0] < 0 or c[1] < 0:
                return False
            if c[0] >= layer1.shape[0] or c[1] >= layer1.shape[1]:
                return False
            return True
        it = np.nditer(layer1, flags=["multi_index", "refs_ok"])
        for tile in it:
            tile = tile.item()
            if tile.tile_type == 9:
                fixed_tiles.add(Coord(*it.multi_index))
        # Add all enemy positions
        #TODO: Some enemies may take up more than one tile...
        #TODO: PLMs may want to have more than one tile allocated too
        for enemy in state.enemy_list.enemies:
            e_pos = Coord(enemy.x_pos//16, enemy.y_pos//16)
            enemy_locale = get_cross(e_pos)
            for p in enemy_locale:
                if inbounds(p):
                    fixed_tiles.add(p)
        # Add PLM positions
        for plm in state.plms.l:
            plm_pos = Coord(plm.x_pos, plm.y_pos)
            plm_locale = get_cross(plm_pos)
            for p in plm_locale:
                if inbounds(p):
                    fixed_tiles.add(p)
        # Add screens that are either fully solid or fully air
        for x in range(layer1.shape[0] // 16):
            for y in range(layer1.shape[1] // 16):
                screen_x = x * 16
                screen_y = y * 16
                screen = layer1[screen_x:screen_x+16,screen_y:screen_y+16]
                test_solid = np.vectorize(lambda x: x.tile_type == 8)
                test_air = np.vectorize(lambda x: x.tile_type == 0)
                if np.all(test_solid(screen)) or np.all(test_air(screen)):
                    # Add this screen and its borders
                    for x_sub in range(-1, 17):
                        for y_sub in range(-1, 17):
                            c = (screen_x + x_sub, screen_y + y_sub)
                            if inbounds(c):
                                fixed_tiles.add(Coord(*c))
                # Add all "valid" screens to the screen map
                else:
                   screen_map.add(Coord(x, y)) 
        # Add level borders
        for x in range(layer1.shape[0]):
            fixed_tiles.add(Coord(x, 0))
            fixed_tiles.add(Coord(x, layer1.shape[1]-1))
        for y in range(layer1.shape[1]):
            fixed_tiles.add(Coord(0, y))
            fixed_tiles.add(Coord(layer1.shape[0]-1, y))
        #TODO: constrain scroll boundaries?
    return fixed_tiles, screen_map

# Add random extra_similarity fixed tiles: some percentage of tiles are fixed
def get_extra_fixed_tiles(rect, fixed_tiles, extra_similarity):
    assert extra_similarity >= 0
    assert extra_similarity <= 1
    border_tiles = set()
    for x in range(rect.start.x, rect.end.x):
        border_tiles.add(Coord(x, rect.start.y))
        border_tiles.add(Coord(x, rect.end.y - 1))
    for y in range(rect.start.y, rect.end.y):
        border_tiles.add(Coord(rect.start.x, y))
        border_tiles.add(Coord(rect.end.x - 1, y))
    free_tiles = rect.as_set() - (fixed_tiles | border_tiles)
    n_fixed = int(len(free_tiles) * extra_similarity)
    extra_fixed_tiles = set(random.sample(free_tiles, n_fixed))
    return extra_fixed_tiles | border_tiles

def rel_fixed_tiles(rect, fixed_tiles):
    rect_set = rect.as_set()
    new_tiles = set()
    # Add the original fixed tiles (relative to the offset of the rect)
    for t in fixed_tiles:
        if t in rect_set:
            new_tiles.add(t - rect.start)
    return new_tiles

def get_mapping(level_from, level_to):
    """ Compute a mapping from one array to another """
    assert level_from.shape == level_to.shape
    m = {}
    for x in range(level_from.shape[0]):
        for y in range(level_from.shape[1]):
            from_t = level_from[x,y]
            to_t = level_to[x,y]
            m[from_t] = to_t
    return m

def map_tiles(level_from, mapping):
    return np.vectorize(mapping.get)(level_from)

#OLD:
#new = np.empty_like(level_from)
#for x in range(level_from.shape[0]):
#    for y in range(level_from.shape[1]):
#        from_t = level_from[x,y]
#        new[x,y] = mapping[from_t]
#return new

def get_state_functions(room_header):
    """ For a given room header, compute a list of [room_header, dict] pairs.
        These dicts provide a mapping between Tile objects so that level data can be 
        effectively translated if the room has multiple states.
        If the room's states all share the same level data, this will be empty.
    """
    default_level_data = room_header.state_chooser.default.level_data
    fns = []
    for state in [s.state for s in room_header.state_chooser.conditions]:
        # No need if they share level data
        if state.level_data is default_level_data:
            continue
        default_dims = default_level_data.level_array.layer1.shape
        state_dims = state.level_data.level_array.layer1.shape
        d_bits = bit_array_from_bytes(default_level_data.level_bytes, default_dims)
        s_bits = bit_array_from_bytes(state.level_data.level_array, state_dims)
        bit_fn = get_mapping(d_bits, s_bits)
        fns.append(state, bit_fn)
    return fns

def level_from_bits(bits):
    new_bytes = bytes_from_bit_array(bits)
    new_arrays = level_array_from_bytes(new_bytes, Coord(*bits.shape[:-1]))
    return new_bytes, new_arrays

def transform_level_data(fn_entry, default_level_bits):
    state, bit_fn = fn_entry
    new_bits = map_tiles(bit_fn, default_level_bits)
    old_level_data = state.level_data
    new_leveldata = state.obj_names.create(LevelData, *level_from_bits(new_bits), None, replace=old_level_data)
    # Fix up pointer for that state
    state.level_data = new_leveldata.name

#TODO: auto-splitting and offset / size
def bit_wfc(level_bits, fixed_tiles):
    """ Perform WFC to create a new tile grid based on default """
    #TODO: move this stuff into Context.__init__?
    width = level_bits.shape[0]
    height = level_bits.shape[1]
    tile_size = 1
    pattern_size = 2
    # Get the tile grid
    # Tile catalog maps from the hash to a 1x1x40 vector, reversing the hashing process
    print("\tGetting tile grid")
    tile_catalog, level_data_tiles, _code_list, _unique_tiles = wfc_tiles.make_tile_catalog(level_bits, tile_size)
    print("\tRect size: {}".format(level_data_tiles.shape))
    adj_rules = None

    # Get the patterns
    # Pattern catalog maps tiles to patterns?
    # Input is not periodic
    print("\tGetting pattern catalog")
    pattern_catalog, pattern_weights, pattern_list, pattern_grid = wfc_patterns.make_pattern_catalog(
                    level_data_tiles, pattern_size, False)
    number_of_patterns = len(pattern_catalog)
    print("\tNumber of patterns: {}".format(number_of_patterns))

    # Get the adjacencies
    print("\tGetting adjacencies")
    directions = list(enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]))
    adjacency_relations = wfc_adjacency.adjacency_extraction(
                    pattern_grid, pattern_catalog, directions)

    # Create functions to make pattern arrays and decode them
    decode_patterns = np.vectorize({x: i for i, x in enumerate(pattern_list)}.get)
    encode_patterns = np.vectorize({i: x for i, x in enumerate(pattern_list)}.get)
    decode_dict = {x:i for i,x in enumerate(pattern_list)}

    # Direction -> list of sets
    adjacency_list = {}
    for i, d in directions:
        adjacency_list[d] = [set() for i in pattern_weights]
    for direction, pattern1, pattern2 in adjacency_relations:
        adjacency_list[direction][decode_dict[pattern1]].add(decode_dict[pattern2])
    # The original level as pattern ids
    pattern_id_grid = decode_patterns(pattern_grid)

    # ASP
    print("\tStarting ASP instance")
    ctl = clingo.Control([], logger=print)
    # WFC constraints
    ctl.add("wfc", ["h","w","p"], """
      cell(0..h-1,0..w-1).
      pattern(0..p-1).
      wave(I,J,K) :- (I,J,K) = @constrained_tiles.
      1 { wave(I,J,P):pattern(P) } 1 :- cell(I,J).
      :- wave(I,J,A), J < w-1, not 1 { wave(I,J+1,@v_adj(A)) }.
      :- wave(I,J,A), I < h-1, not 1 { wave(I+1,J,@h_adj(A)) }.
      %:- pattern(P), not 1 { wave(I,J,P) }. % Every tile must be used at least once
      #show wave/3.
    """)
    ctx = Context(width, height, adjacency_list)
    #TODO: swap axes?
    for t in fixed_tiles:
        ctx.pin_tile(t[1], t[0], pattern_id_grid)
    print("\tGrounding ASP Model")
    ctl.ground([("wfc", list(map(clingo.Number,[height, width, number_of_patterns])))], context=ctx)
    print("\tSolving ASP Model")
    #TODO: --restart_on_model, Config object?
    #TODO: Specify seed to ASP config?
    #TODO: Constrain the amount of plagiarism?
    ctl.solve(on_model=ctx.on_model)
    solution = ctx.solution
    # Convert to pattern array
    solution_as_ids = encode_patterns(solution)
    # Convert to tile hash array
    solution_tile_grid = wfc_patterns.pattern_grid_to_tiles(solution_as_ids, pattern_catalog)
    output = np.zeros((height, width, level_bits.shape[2]))
    # Convert back to bit array
    #TODO: swap axes?
    for y in range(height):
        for x in range(width):
            output[y,x,:] = tile_catalog[solution_tile_grid[y,x]]
    output = np.swapaxes(output, 0, 1)
    assert output.shape == level_bits.shape
    # Convert to int
    output = output.astype("int64")
    return output

#TODO: If there is a level 2, add an option for considering it independently
# generating layer 1 without respect to layer 2
def wfc_and_create(room_header, auto_rect=False, rects=None, extra_similarity=0):
    # Get fns before messing with the level data
    fns = get_state_functions(room_header)
    fixed_tiles, screen_map = get_fixed_tiles(room_header)
    default_level_data = room_header.state_chooser.default.level_data
    level_shape = Coord(*default_level_data.level_array.layer1.shape)
    level_bits = bit_array_from_bytes(default_level_data.level_bytes, level_shape)
    # Get the rectangularization either automatically, by input, or just the whole level at once
    if auto_rect:
        assert rects is None
        # Scale them back up to size 16x16 (rects found are rects of screens)
        #TODO: choose tiles based on ratio of tiles / pattern (higher is better)
        rects = [rect.scale(16) for rect in wfc_rectangularize(screen_map, max_area=9)]
        print("Found rectangles: {}".format(rects))
    # Use one big rect if none is satisfied
    elif rects is None:
        offset = Coord(0,0)
        size = Coord(*level_shape)
        rects = [Rect(offset, size)]
    # Use WFC to reconstruct each rect using tiles from within that rect
    #TODO: how to use tiles from the entire room?
    for rect in rects:
        print("For rectangle {}:".format(rect))
        # Add borders etc.
        extra_fixed_tiles = get_extra_fixed_tiles(rect, fixed_tiles, extra_similarity)
        all_fixed_tiles = fixed_tiles | extra_fixed_tiles
        rect_bits = level_bits[rect.start[0]:rect.end[0],rect.start[1]:rect.end[1]]
        rect_fixed_tiles = rel_fixed_tiles(rect, all_fixed_tiles)
        #print(rect_fixed_tiles)
        print("Fixed tile ratio: {}".format(len(rect_fixed_tiles) / rect.area))
        wfc_bits = bit_wfc(rect_bits, rect_fixed_tiles)
        # Overwrite level_bits with the new data
        level_bits[rect.start[0]:rect.end[0],rect.start[1]:rect.end[1]] = wfc_bits
    #TODO: instead of create, assign to the existing level data
    old_level_data = room_header.state_chooser.default.level_data
    wfc_level_data = room_header.obj_names.create(LevelData, *level_from_bits(level_bits), None, replace=old_level_data)
    # Fix up default pointer
    room_header.state_chooser.default.level_data = wfc_level_data.name
    # Use the fns to compute new per-state level data and register it
    for entry in fns:
        transform_level_data(entry, level_bits)

class Context():

  def __init__(self, width, height, adjacency_list):
    self._constrained_tiles = []
    self._t_constrained_tiles = []
    self.width = width
    self.height = height
    self.adjacency_list = adjacency_list

  def h_adj(self, a):
    return [clingo.Number(b) for b in self.adjacency_list[(1,0)][a.number]]

  def v_adj(self, a):
    return [clingo.Number(b) for b in self.adjacency_list[(0,1)][a.number]]

  def on_model(self, model):
    solution = np.zeros((self.height, self.width),dtype=int)
    for s in model.symbols(shown=True):
      if s.name == 'wave':
        i,j,k = [x.number for x in s.arguments]
        solution[i,j] = k
    self.solution = solution

  def constrained_tiles(self):
    return self._constrained_tiles

  def pin_tile(self, y, x, pidgrid):
    original_pattern = pidgrid[x][y]
    t = clingo.Tuple_((clingo.Number(y), clingo.Number(x), clingo.Number(original_pattern)))
    self._constrained_tiles.append(t)
    self._t_constrained_tiles.append((y,x))


