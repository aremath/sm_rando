from pathlib import Path

import parse_rules
import search

def run_test(output_folder, rules, test_name, tests):
    print("Doing Test: {}".format(test_name))
    i,f = tests[test_name]
    offers, finished, final_state = search.rule_search(i, rules.values(), f)
    if final_state is not None:
        print("Final state found!")
        path = search.get_path(offers, i, f)
        print("Using:")
        print([p.name for p in path])
        out_image = final_state.to_image()
        out_path = output_folder / (test_name + "_out.png")
        out_image.save(out_path)
    else:
        print("Final state not found!")

def run_all_tests(rules_folder, rules, tests):
    for test_name in tests.keys():
        run_test(rules_folder, rules, test_name, tests)

if __name__ == "__main__":
    rules_files = ["../encoding/rules/rules.yaml", "../encoding/rules/model_checking_tests/model_checking_tests.yaml"]
    output_folder = Path("../output/")
    rules, tests = parse_rules.parse_rules(rules_files)
    #run_all_tests(output_folder, rules, tests)
    #run_test(output_folder, rules, "TestBombJump", tests)
    #run_test(output_folder, rules, "TestGrabBombs", tests)
    run_test(output_folder, rules, "ConstructionZone", tests)
