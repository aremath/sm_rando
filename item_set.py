# 36 items -> 64 bit set?
# does python guarantee storage in 64 bit integers rather than some weird thing?
item_mapping = {
    "B" : 1,
    "PB" : 1 << 1,
    "SPB" : 1 << 2,
    "S" : 1 << 3,
    "M" : 1 << 4,
    "G" : 1 << 5,
    "SA" : 1 << 6,
    "V" : 1 << 7,
    "GS" : 1 << 8,
    "SB" : 1 << 9,
    "HJ" : 1 << 10,
    "MB" : 1 << 11,
    "CB" : 1 << 12,
    "WB" : 1 << 13,
    "E" : 1 << 14,
    "PLB" : 1 << 15,
    "Spazer" : 1 << 16,
    "RT" : 1 << 17,
    "XR" : 1 << 18,
    "IB" : 1 << 19,
    "SJ" : 1 << 20,
    "Kraid" : 1 << 21,
    "Phantoon" : 1 << 22,
    "Draygon" : 1 << 23,
    "Ridley" : 1 << 24,
    "Botwoon" : 1 << 25,
    "Spore_Spawn" : 1 << 26,
    "Golden_Torizo" : 1 << 27,
    "Bomb_Torizo" : 1 << 28,
    "Mother_Brain" : 1 << 29,
    "Crocomire" : 1 << 30,
    "Ceres_Ridley" : 1 << 31,
    "Drain" : 1 << 32,
    "Shaktool" : 1 << 33,
    "START" : 1 << 34,
}

class ItemSet(object):

    def __init__(self, item_list=[], num_=0):
        self.num = num_
        for item in item_list:
            self.num |= item_mapping[item]

    # modification
    def add(self, item):
        self.num |= item_mapping[item]

    def remove(self, item):
        item_mask = item_mapping[item]
        assert self.num & item_mask != 0, "Remove: not in set"
        self.num &= (~item_mask)

    # set union
    def __or__(self, other):
       return ItemSet([], self.num | other.num)

    # set intersection
    def __and__(self, other):
        return ItemSet([], self.num & other.num)

    # comparison
    def __eq__(self, other):
        return self.num == other.num

    # subset
    def __le__(self, other):
        # s is a subset of o of adding s to o adds nothing
        return (self.num | other.num) == other.num

    def __ge__(self, other):
        return other <= self

    def __ne__ (self, other):
        return not self == other

    # BE CAREFUL! ItemSet is mutable but also hashable!
    def __hash__(self):
        return hash(self.num)

    def to_list(self):
        slist = []
        for item, mask in item_mapping.items():
            if self.num & mask != 0:
                slist.append(item)
        return slist

    def __repr__(self):
        return "ISet(" + str(self.to_list()) + ")"

