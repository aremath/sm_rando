from item_set import *
#TODO: more?

if __name__ == "__main__":
    iset = ItemSet(["Kraid", "START"])
    assert "Kraid" in iset, iset.num
    assert "START" in iset, iset.num
