import random
# Python3 automatically randomizes string hash function to avoid collision attacks.
# To make RNG work properly, we need a hash function that will always do the same thing.
import hashlib

def seed_rng(seed):
    # Choose four randomly chosen sm words if no seed is provided
    if seed is None:
        # Re-seed it with the system time first to prevent the
        # order of seeds being fixed by the original seed.
        random.seed()
        with open("misc/sm_words") as f:
            l = f.read().splitlines()
            words = random.choices(l, k=4)
            sm_sentence = ", ".join(words)
            random.seed(get_hash(sm_sentence))
            return sm_sentence
    else:
        random.seed(get_hash(seed))
        return seed

def get_hash(s):
    h = hashlib.sha256(s.encode())
    v = int.from_bytes(h.digest(), "big")
    return v
