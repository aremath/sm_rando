# Credit to Raymond Hettinger (https://code.activestate.com/recipes/576694/)
import collections

# Import MutableSet from abc submodule if we need to
if hasattr(collections, "MutableSet"):
    MutableSet = collections.MutableSet
else:
    from collections.abc import MutableSet


class OrderedSet(MutableSet):

    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def copy(self):
        c = OrderedSet(self)
        return c

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)


def test_OrderedSet():
    s = OrderedSet('abracadaba')
    t = OrderedSet('simsalabim')
    union = s | t
    intersection = s & t
    diff1 = s - t
    diff2 = t - s
    assert union == { 'a', 'b', 'r', 'c', 'd', 's', 'i', 'm', 'l' }
    assert intersection == { 'a', 'b' }
    assert diff1 == { 'r', 'c', 'd' }
    assert diff2 == { 's', 'i', 'm', 'l' }
    assert list(union) == ['a', 'b', 'r', 'c', 'd', 's', 'i', 'm', 'l']
    assert list(intersection) == ['a', 'b']
    assert list(diff1) == ['r', 'c', 'd']
    assert list(diff2) == ['s', 'i', 'm', 'l']

    t2 = OrderedSet('lmsbai')
    assert t2 == set(t)
    assert set(t2) == t
    assert t2 != t
    assert list(t2) != list(t)
    assert list(t2) == [ 'l', 'm', 's', 'b', 'a', 'i' ]

    assert list(t2 - s) == ['l', 'm', 's', 'i']
    assert list(s - t2) == ['r', 'c', 'd']


if __name__ == '__main__':
    test_OrderedSet()
