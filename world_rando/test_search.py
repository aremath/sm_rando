from pathlib import Path

import parse_rules
import search

if __name__ == "__main__":
    rules_file = Path("../encoding/rules/rules.txt")
    rules_folder = rules_file.parents[0]
    rules, tests = parse_rules.parse_rules(rules_file)
    for test_name, (i,f) in tests.items():
        offers, finished, final_state = search.rule_search(i, rules.values(), f)
        if final_state is not None:
            out_image = final_state.to_image()
            out_path = rules_folder / (test_name + "_out.png")
            out_image.save(out_path)
        else:
            print("Final state not found!")
            
