import itertools
from collections import defaultdict
from tqdm import tqdm
import random
import functools
import imageio
import networkx as nx
import numpy as np

from abstraction_validation.abstractify import abstractify_state

class cachedict(defaultdict):
	def __missing__(self, key):
		if self.default_factory is None:
			raise KeyError(key)
		else:
			value = self.default_factory(key)
			self[key] = value
			return value

def pairwise(iterable):
    "s -> (s0, s1), (s1, s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

def resimulate(emu, path, graph):
    """
    Resimulate a path through a go-explore graph, while also checking that the path is valid
    """
    emu.set_state(path[0])
    frames = []
    for p1, p2 in pairwise(path):
        input, n_steps = graph[p1][p2]["action"]
        for _ in range(n_steps):
            emu.set_button_mask(input,0)
            emu.step()
            frames.append(emu.get_screen())
        assert emu.get_state() == p2
    return frames

def resim_and_write(emu, path, graph, fname="sm.gif", framespeed=1, imscale=1):
    frames = resimulate(emu, path, graph)
    frames = np.array(frames)
    print(f"Length: {len(path)} states, {len(frames)} frames")
    imageio.mimwrite(fname, frames[::framespeed,::imscale,::imscale], format="gif", fps=(60 // framespeed))

class Selector(object):

    def __init__(self):
        pass

    def select(self, cells):
        return random.choice(cells)

class SoftminSelector(Selector):

    def __init__(self, weight_fun):
        # Cache cell distance for faster computation
        self.cache = cachedict(weight_fun)

    def select(self, cells):
        dists = np.array([self.cache[cell] for cell in cells])
        # Softmin
        weights = np.exp(-dists/3) / np.sum(np.exp(-dists/3))
        cell = random.choices(cells, weights, k=1)[0]
        return cell

class MarkovSelector(Selector):

    def __init__(self, model, background):
        # Action -> ([float])
        # How often did each action occur after the current action
        # Must be in the same order as the action list
        # Must include an entry None for the background (unconditional) distribution
        self.model = model
        self.prev_action = None
    
    def select(self, actions):
        random.choices(actions, self.background, k=1)[0]

def go_explore(initial_state, actions, emu, gamedata, n_steps, max_step_size, cell_ok=lambda x: True,  goal=lambda s: False, cell_selector=Selector(), action_selector=Selector(), global_pos=False, seed=None):
    if seed is not None:
        random.seed(seed)
    #  Graph of Real State, with actions on edges
    graph = nx.Graph()
    # Abstract State -> Set(Real State) 
    atlas = defaultdict(set)
    emu.set_state(initial_state)
    ram = np.frombuffer(gamedata.memory.blocks[0x7e0000],'int16')
    graph.add_node(initial_state, ram=ram)
    initial_cell = abstractify_state(ram, global_pos)
    print(initial_cell)
    atlas[initial_cell] = set([initial_state])
    cell = None
    for _ in tqdm(range(n_steps), unit="step"):
        all_cells = list(atlas.keys())
        cell = cell_selector.select(all_cells)
        if goal(cell):
            break
        state = random.choice(list(atlas[cell]))
        #TODO make action selector also choose the number of steps
        action = action_selector.select(actions)
        emu.set_state(state)
        n_steps = random.randint(1, max_step_size)
        for _  in range(n_steps):
            emu.set_button_mask(action,0)
            emu.step()
        ram = np.frombuffer(gamedata.memory.blocks[0x7e0000],'int16')
        next_cell = abstractify_state(ram, global_pos)
        # Bounds checking using cell_ok
        if cell_ok(next_cell):
            next_state = emu.get_state()
            graph.add_node(next_state, ram=ram)
            graph.add_edge(state, next_state, action=(action, n_steps))
            atlas[next_cell].add(next_state)
    return atlas, graph, cell, initial_cell
