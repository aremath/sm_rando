import random
from itertools import tee

# Credit to Weighted Random Sampling, Efraimidis, Spirakis 2005
def weighted_random_order(l, weights, n=None):
    assert len(l) == len(weights)
    # Handle the zero weight elements separately
    l, weights, zero_l = split_zeros(l, weights)
    # Find a shuffling of the nonzero elements based on weight
    order = sorted(range(len(l)), key=lambda i: -random.random() ** (1.0 / weights[i]))
    new_l = [l[i] for i in order]
    # Randomize the zero elements
    random.shuffle(zero_l)
    ordered_l = new_l + zero_l
    if n is None:
        return ordered_l
    else:
        return ordered_l[:n]

# Split l into two lists, the second list has the elements of weight zero
def split_zeros(l, weights):
    l_new = []
    w_new = []
    zero_l = []
    for i in range(len(l)):
        if weights[i] == 0:
            zero_l.append(l[i])
        else:
            l_new.append(l[i])
            w_new.append(weights[i])
    return l_new, w_new, zero_l

# Iterate through an iterable by pairs
def pairwise(iterable):
    a,b = tee(iterable)
    next(b, None)
    return zip(a,b)
