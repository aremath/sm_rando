from item_constraints import *

if __name__ == "__main__":
    preds = parse_preds("dsl/item_order.txt")
    print choose_order(preds, all_things)
