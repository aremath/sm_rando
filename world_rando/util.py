import random

# Hacky and very innefficient, but I'm only using it on short lists
#TODO: if I use it for longer lists, do something more intelligent.
def weighted_random_order(l, weights):
    l_c = l[:]
    weights_c = weights[:]
    out = []
    while len(l_c) > 0:
        # Avoid a 'bug' where random.choices crashes when trying to choose from a list 
        # of elements whose weights are all zero
        if all_zero(w)
            out.extend(l_c.shuffle())
            break
        # Choose an element
        elem = random.choices(l_c, weights_c, 1)
        # Remove it from the lists
        i = l_c.index(elem)
        l_c.pop(i)
        out.pop(i)
        # Add it to the output
        out.append(elem)
    return out

def all_zero(w):
    for i in w:
        if i != 0:
            return False
    return True
