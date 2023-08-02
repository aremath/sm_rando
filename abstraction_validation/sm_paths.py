import clingo
from bidict import bidict
import networkx as nx
import numpy as np
import re

from data_types.item_set import ItemSet
from encoding.parse_rooms import parse_rooms, parse_exits, dictify_rooms
from collections import defaultdict
from world_rando.parse_rules import mk_plm_to_item
from rom_tools.item_definitions import make_item_definitions
from world_rando.parse_rules import get_item_locations # returns Coord -> ItemSet mapping
from abstraction_validation.abstractify import area_offsets
from world_rando.coord import Coord

def symbol(**kwargs):
    assert len(kwargs) == 1
    for tag, ident in kwargs.items(): 
        prefix = ""#tag + "_"
        return prefix + re.sub('[^_a-z0-9]','',ident.lower())

# ../output/metroidIII.lp
def mk_asp_logicfile(design, filename):
    condition_ids = {}
    with open(filename, 'w') as f:

        for item_name, item_description in design['Items'].items():
            f.write(f"item({symbol(item=item_name)}).\n")

        for boss_name, boss_description in design['Bosses'].items():
            f.write(f"boss({symbol(item=boss_name)}).\n")

        for room_name, room in design['Rooms'].items():
            f.write(f"room({symbol(room=room_name)}).\n")

            for node_name in room['Nodes']:
                f.write(f"node({symbol(room=room_name)},{symbol(node=node_name)}).\n")

            for node_name, item_name in room['Drops'].items():
                f.write(f"drops({symbol(room=room_name)},{symbol(node=node_name)},{symbol(item=item_name)}).\n")

            for src_node, dst_spec in room['Doors'].items():
                dst_room = dst_spec['Room']
                dst_node = dst_spec['Node']
                f.write(f"door({symbol(room=room_name)},{symbol(node=src_node)},{symbol(room=dst_room)},{symbol(node=dst_node)}).\n")

            for src_node, edges in room['Edges'].items():
                for dst_spec in edges:
                    dst_node = dst_spec['Terminal']
                    f.write(f"edge({symbol(room=room_name)},{symbol(node=src_node)},{symbol(node=dst_node)}).\n")  
                    for i, requirements in enumerate(dst_spec['Requirements']):
                        requirements_tuple = tuple(requirements)
                        if requirements_tuple not in condition_ids:
                            n = len(condition_ids)
                            f.write(f"condition({n}).\n")
                            for item in requirements:
                                f.write(f"condition_requires({n},{symbol(item=item)}).\n")
                            condition_ids[requirements_tuple] = n
                        n = condition_ids[requirements_tuple]
                        f.write(f"edge_condition({symbol(room=room_name)},{symbol(node=src_node)},{symbol(node=dst_node)},{n}).\n")

# ../output/metroidIII.lp
# ../output/path.lp

def get_room_name_mapping(design):
    # Maps the "common" name of a node to the name that ASP will use (and vice versa)
    room_name_mapping = bidict({})
    for room_name, room in design["Rooms"].items():
        for node_name in room["Nodes"]:
            node_full_name = f"{room_name}_{node_name}"
            node_asp_name = (symbol(room=room_name), symbol(node=node_name))
            room_name_mapping[node_full_name] = node_asp_name

# Set up control with the actual problem
#TODO: do this with a Context
def mk_conditions(start_position, start_item_set, end_position, end_item_set):
    # Start conditions
    r, n = room_name_mapping[start_position]
    start_pos = [f"step(0, {r}, {n})."]
    i_names = [symbol(item=i) for i in start_item_set]
    start_items = [f"(has(0,{i})." for i in i_names]
    start_constraint = "\n".join(start_items + ["has(0, start)."] + start_pos)
    # End conditions
    i_names = [symbol(item=i) for i in end_item_set]
    end_items = [f"has(T,{i})" for i in i_names]
    r, n = room_name_mapping[end_position]
    end_pos = [f"reach(T, {r}, {n})"]
    end_constraint = ", ".join(end_items + end_pos)
    end_constraint = f"goal(T) :- {end_constraint}.\ngoal :- goal(T).\n:- not goal."
    return start_constraint + "\n" + end_constraint

def parse_policy(p, g):
    t, r1, n1, r2, n2 = p.arguments
    #print(int(t), r1, n1, r2, n2)
    t = t.number
    node1 = (t, r1.name, n1.name)
    node2 = (t, r2.name, n2.name)
    g.add_edge(node1, node2)

def parse_step(s, g):
    t, r, n = s.arguments
    t = t.number
    print(s)
    node1 = (t-1, r.name, n.name)
    node2 = (t, r.name, n.name)
    g.add_edge(node1, node2)

class Context(object):

    def __init__(self, start_pos, start_itemset, end_pos, end_itemset, room_name_mapping):
        # Start
        self.start_pos = start_pos
        r, n = room_name_mapping[start_pos]
        self.asp_start_pos = (clingo.Symbol(r), clingo.Symbol(n))
        self.start_itemset = start_itemset
        self.asp_start_itemset = [clingo.Symbol(symbol(item=i)) for i in start_itemset]
        # End
        self.end_pos = end_pos
        r, n = room_name_mapping[end_pos]
        self.asp_end_pos = (clingo.Symbol(r), clingo.Symbol(n))
        self.end_itemset = end_itemset
        self.asp_end_itemset = [clingo.Symbol(symbol(item=i)) for i in end_itemset]
        # Other
        self.graph = None

    # Only need one path
    def on_model(self, model):
        g = nx.Graph()
        for s in model.symbols(shown=True):
            if s.name == "policy":
                parse_policy(s, g)
            if s.name == "step":
                parse_step(s, g)
        self.graph = g

    def starting_position(self, r, n):
        return self.asp_start_pos

    def ending_position(self, r, n):
        return self.asp_end_pos

    def starting_item(self, i):
        return [clingo.Symbol(i) for i in self.asp_start_itemset]
  
    def ending_item(self, i):
        return [clingo.Symbol(i) for i in self.asp_end_itemset]

    def get_end_t(self):
        assert self.graph is not None
        ends = [n for n in self.graph.nodes if n[1:] == room_name_mapping[self.end_pos]]
        # Node with the max step is the last time we visit this node
        m = max(ends, key=lambda n: n[0])
        return m

    def get_path(self):
        assert self.graph is not None
        start = (0, *room_name_mapping[self.start_pos])
        end = self.get_end_t()
        #print(start, end)
        path  = nx.shortest_path(self.graph, source=start, target=end)
        return path
        # Go back to "common" names
        #return [room_name_mapping.inverse[p[1:]] for p in path]

    def solve_path(self):
        # Set up control with the objects
        ctl = clingo.Control([], logger=print)
        with open('../output/metroidIII.lp', 'r') as f:
            metroid3_s = "\n".join(f.readlines())
        ctl.add("metroid3", [], metroid3_s)
        # Set up control with the path constraints
        with open('../output/path.lp', 'r') as f:
            path_s = "\n".join(f.readlines())
        ctl.add("path", [], path_s)
        ctl.add("initial", [], mk_conditions(self.start_pos, self.start_itemset, \
                                             self.end_pos, self.end_itemset))
        ctl.ground([("metroid3", []), ("path", []), ("initial", [])])#, context=self)
        ctl.solve(on_model=self.on_model)
        path = self.get_path()
        return path
        #return [room_name_mapping.inverse[p[1:]] for p in path]

#TODO: temporary until push changes for sm_rando
def get_item_locations(plms):
        item_locations = {}
        plm_to_item = mk_plm_to_item(make_item_definitions())
        for plm in plms.l:
                if plm.plm_id in plm_to_item:
                        iset = plm_to_item[plm.plm_id]
                        c = Coord(plm.x_pos, plm.y_pos)
                        item_locations[c] = iset
        return item_locations

def get_door_positions(level_arrays, ignore_locs):
        # Find the door positions
        doors = defaultdict(list)
        for i, j in np.ndenumerate(level_arrays.layer1):
                if i in ignore_locs:
                        continue
                if j.tile_type == 9:
                        door_id = level_arrays.bts[i]
                        doors[door_id].append(Coord(*i))
        return doors

def get_door_averages(doors):
        # Find the door average position
        door_a = {}
        for i, cs in doors.items():
                cxa = sum([c.x for c in cs]) / len(cs)
                cxy = sum([c.y for c in cs]) / len(cs)
                c_a = Coord(cxa, cxy)
                door_a[i] = c_a
        return door_a

def get_door_directions(doors, door_a, level_arrays):
        sand_tindices = [280, 528, 640]
        # Find the direction for each door
        door_d = {}
        ls = []
        rs = []
        ts = []
        bs = []
        for d, a in door_a.items():
                #print(d, a)
                # Left door
                if a.x % 16 == 0:
                        if len(doors[d]) == 1:
                                door_d[d] = "LMB{}"
                        else:
                                door_d[d] = "L{}"
                        ls.append(d)
                # Right door
                elif a.x % 16 == 15:
                        if len(doors[d]) == 1:
                                door_d[d] = "RMB{}"
                        else:
                                door_d[d] = "R{}"
                        rs.append(d)
                # Top door
                elif a.y % 16 == 0:
                        if level_arrays.layer1[doors[d][0]].texture.texture_index in sand_tindices:
                                door_d[d] == "TS{}"
                        elif len(doors[d]) == 2:
                                door_d[d] = "EB{}"
                        else:
                                door_d[d] = "T{}"
                        ts.append(d)
                # Bottom door
                elif a.y % 16 == 15:
                        if level_arrays.layer1[doors[d][0]].texture.texture_index in sand_tindices:
                                door_d[d] = "BS{}"
                        elif len(doors[d]) == 2:
                                door_d[d] = "ET{}"
                        else:
                                door_d[d] = "B{}"
                        bs.append(d)
                else:
                        # Elevator
                        if len(doors[d]) == 2:
                                pass
                        else:
                                assert False, f"No direction found for door {d}!"
        return (ls, rs, ts, bs), door_d

def compute_name_positions(door_lists, doors, door_a, door_d):
        # Sort everything and compute positions
        ls, rs, ts, bs = door_lists
        ls = sorted(ls, key = lambda d: door_a[d].y)
        rs = sorted(rs, key = lambda d: door_a[d].y)
        ts = sorted(ts, key = lambda d: door_a[d].x)
        bs = sorted(bs, key = lambda d: door_a[d].x)
        name_posns = {}
        def convert_names(ls):
                for i,l in enumerate(ls):
                        f = i + 1
                        if len(ls) == 1:
                                f = ""
                        name_posns[door_d[l].format(f)] = door_a[l]
        convert_names(ls)
        convert_names(rs)
        convert_names(ts)
        convert_names(bs)
        return name_posns

def get_all_item_positions(room_header):
        item_posns = {}
        for rs in [x.state for x in room_header.state_chooser.conditions] + [room_header.state_chooser.default]:
                d = get_item_locations(rs.plms)
                item_posns.update(d)
        return item_posns

def get_item_names(item_positions):
        item_d = defaultdict(list)
        for k, v in item_positions.items():
                assert len(v) == 1
                item_str = item_str = v.to_list()[0]
                item_d[item_str].append(k)
        item_names = {}
        for i, posns in item_d.items():
                if len(posns) == 1:
                        item_names[i] = posns[0]
                else:
                        #TODO: these may not actually refer to the same item!
                        # But there are very few rooms with the same type of item twice...
                        for j, p in enumerate(sorted(posns)):
                                item_names[f"{i}{j+1}"] = p
        return item_names

#TODO items
def get_locations(parsed, room, ignore_locs=[], is_global=True):
        room_header = parsed[f"room_header_{hex(room.mem_address)}"]
        area_pos = area_offsets[room_header.area_index]
        room_map_pos = Coord(room_header.map_x, room_header.map_y)
        #print(area_pos, room_map_pos)
        if is_global:
            global_offset = (area_pos + room_map_pos).scale(16)
        else:
            global_offset = Coord(0,0)
        name_posns = {}
        # PLMs
        item_d = get_all_item_positions(room_header)
        item_names = get_item_names(item_d)
        for k,v in item_names.items():
            name_posns[f"{room.name}_{k}"] = v + global_offset
        # Doors
        level_arrays = room_header.state_chooser.default.level_data.level_array
        doors = get_door_positions(level_arrays, ignore_locs)
        door_a = get_door_averages(doors)
        #print(doors)
        #print(door_a)
        door_lists, door_d = get_door_directions(doors, door_a, level_arrays)
        door_posns = compute_name_positions(door_lists, doors, door_a, door_d)
        global_door_posns = {f"{room.name}_{k}": v + global_offset for k,v in door_posns.items()}
        name_posns.update(global_door_posns)
        return name_posns

ignore_locs = {
    "West_Ocean": [(48,38), (48,39), (48,40), (48,41), (80,38), (80,39), (80,40), (80,41),
                   (79,38), (79,39), (79,40), (79,41), (95,38), (95,39), (95,40), (95,41)],
    "Mount_Everest": [(15, 41),
                      (86,32), (87,32), (88,32), (89,32)],
    "Plasma_Spark": [(0,41), (48,22), (48,23), (48,24), (48,25)],
    "Pseudo_Plasma_Spark": [(63, 9)]
}

# TS will be missing
# Bombs will be missing - Bombs / B error again
# Boss nodes will be missing
# Mother Brain L
# Outside of this - Parsing errors:
# West_Ocean
# R4 -> R6 and L -> L2

def all_global_positions(rooms, parsed_rom):
    return all_positions(rooms, parsed_rom, is_global=True)

# Returns a mapping from node name to position
def all_positions(rooms, parsed_rom, is_global=True):
        all_positions = {}
        for room_name, r in rooms.items():
                if room_name in ignore_locs:
                        i = ignore_locs[room_name]
                else:
                        i = []
                d = get_locations(parsed_rom, r, i, is_global)
                all_positions.update(d)
                gp_nodes = set(d.keys())
                r_nodes = set(r.graph.nodes)
                if gp_nodes != r_nodes:
                        print(room_name, hex(r.mem_address))
                        print(f"\t Extra: {list(gp_nodes - r_nodes)}")
                        print(f"\t Missing: {list(r_nodes - gp_nodes)}")
        return all_positions

def get_drop_table(design):
    # (room, node) -> item_name
    drop_table = {}
    for room_name, room in design['Rooms'].items():
        for node_name, item_name in room['Drops'].items():
            drop_table[(symbol(room=room_name), symbol(node=node_name))] = item_name

def get_intervals(path, drop_table):
    intervals = {}
    current_t = 0
    current_index = 0
    for (i, (t, r, n)) in enumerate(path):
        if t != current_t:
            intervals.append(((current_index, i), drop_table[(r, n)]))
            current_t = t
            current_index = i
    intervals.append(((current_index, i), "END"))
    return intervals

def get_intervals_dict(path, path_intervals):
        i = {}
        items = ItemSet()
        for (start, end), item in path_intervals:
                i[items] = path[start:end]
                items = items | ItemSet([item])
        return i

def get_annotated_path(path, path_intervals):
        # [(node, itemset)]
        apath = []
        items = ItemSet()
        for (start, end), item in path_intervals:
                for p in path[start:end]:
                        apath.append(p, items)
                items = items | ItemSet([item])
        return apath

#TODO: use room information (player must be in the same room as the node that they are at)
def map_state_to_node(state, node_positions):
        ds = [(state.position.euclidean(p), k) for k, p in node_positions.items()]
        return min(sorted(ds, key=lambda x: x[0]))
