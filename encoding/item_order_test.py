from item_order import *
import sm_global

if __name__ == "__main__":
    preds = parse_preds("dsl/item_order.txt")
    print choose_order(preds, sm_global.all_things)
