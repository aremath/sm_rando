# parses the free_space.txt file from dsl. The format is very simple.
from pathlib import Path

def get_frees(filename):
    f = open(filename, "r")
    extents = []
    for line in f.readlines():
        if line[0] == "\n":
            continue
        if line[0] == "#":
            continue
        else:
            start, end = line.split("|")
            start = int(start, 16)
            end = int(end, 16)
            size = end-start
            assert size > 0
            extents.append((start, size))
    return extents

def find_free_space():
    return get_frees(Path(__file__).parent / "dsl/free_space.txt")
