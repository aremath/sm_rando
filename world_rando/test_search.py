from pathlib import Path

import parse_rules
import search

def run_test(rules_folder, rules, test_name, tests):
    print("Doing Test: {}".format(test_name))
    i,f = tests[test_name]
    offers, finished, final_state = search.rule_search(i, rules.values(), f)
    if final_state is not None:
        out_image = final_state.to_image()
        out_path = rules_folder / (test_name + "_out.png")
        out_image.save(out_path)
    else:
        print("Final state not found!")

def run_all_tests(rules_folder, rules, tests):
    for test_name in tests.keys():
        run_test(rules_folder, rules, test_name, tests)

if __name__ == "__main__":
    rules_file = Path("../encoding/rules/rules.txt")
    rules_folder = rules_file.parents[0]
    rules, tests = parse_rules.parse_rules(rules_file)
    #run_all_tests(rules_folder, rules, tests)
    run_test(rules_folder, rules, "TestWalk_h", tests)
