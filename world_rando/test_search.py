from pathlib import Path

import parse_rules
import search

finished_color = (0, 255, 0)

def run_test(output_folder, rules, test_name, tests):
    print("Doing Test: {}".format(test_name))
    i,f = tests[test_name]
    offers, finished, final_state = search.rule_search(i, rules.values(), f)
    if final_state is not None:
        print("Final state found!")
        rule_path, state_path = search.get_path(offers, i, f)
        print("Using:")
        print([p.name for p in rule_path])
        print(len(rule_path))
        # Print the final level state
        out_image = final_state.to_image()
        out_path = output_folder / (test_name + "_out.png")
        out_image.save(out_path)
        # Pretty-print the path:
        samus_state_path = [p.samus for p in state_path]
        out_pretty = final_state.level.pretty_print(samus_state_path, "../encoding/levelstate_tiles")
        out_pretty_path = output_folder / (test_name + "_out_pretty.png")
        out_pretty.save(out_pretty_path)
    else:
        print("Final state not found!")
    all_positions = set([s.samus.position for s in finished])
    reached_image = i.to_image(all_positions, finished_color)
    out_path = output_folder / (test_name + "_reached.png")
    reached_image.save(out_path)

def run_all_tests(rules_folder, rules, tests):
    for test_name in tests.keys():
        run_test(rules_folder, rules, test_name, tests)

if __name__ == "__main__":
    rules_files = ["../encoding/rules/rules.yaml", "../encoding/rules/model_checking_tests/model_checking_tests.yaml"]
    output_folder = Path("../output/")
    rules, tests = parse_rules.parse_rules(rules_files)
    #run_all_tests(output_folder, rules, tests)
    #run_test(output_folder, rules, "TestBombJump", tests)
    #run_test(output_folder, rules, "TestGrabMorph", tests)
    run_test(output_folder, rules, "ConstructionZone", tests)
    #run_test(output_folder, rules, "ConstructionSub", tests)
