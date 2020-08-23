import parse_rules

if __name__ == "__main__":
    rules, _ = parse_rules.parse_rules("../encoding/rules/rules.txt")
    print(rules)
