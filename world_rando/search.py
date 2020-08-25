import heapq

block_cost = 0
cost_weight = 0.5
max_rules = 10

def rule_search(start_state, rules, goal_state):
    print("Search to reach {} from {}".format(goal_state.position, start_state.samus.position))
    offers = {}
    finished = set()
    entry_count = 0
    h = [(0, entry_count, start_state)]
    n_rules = 0
    while len(h) != 0:
        n_rules += 1
        priority, _, state = heapq.heappop(h)
        print("Was at: {}".format(state.samus.position))
        next_states = [(r, state.apply_rule(r)) for r in rules]
        for rule, (next_state, n_changed, err) in next_states:
            if next_state is not None:
                print("Applied rule: {} at level {}".format(rule.name, n_rules))
                print("Now at: {}".format(next_state.samus.position))
                statestr = "{}_{}".format(n_rules, rule.name)
                fname = "../output/rule_{}.png".format(statestr)
                state_img = next_state.to_image()
                state_img.save(fname)
                # Mark it
                finished.add(next_state)
                offers[next_state] = state
                #TODO: requiring equality may be too much
                # >=?
                if next_state.samus == goal_state:
                    return offers, finished, next_state
                distance = next_state.samus.position.euclidean(goal_state.position)
                cost = block_cost * n_changed + rule.cost
                # Lower distance is good, lower cost is good
                priority = cost_weight * cost + (1 - cost_weight) * distance
                print(n_changed)
                print(distance)
                print(priority)
                heapq.heappush(h, (priority, entry_count, next_state))
                entry_count += 1
            else:
                print("Rule failed: {}".format(rule.name))
                print("Because: {}".format(err))
        if n_rules >= max_rules:
            print("Applied {} rules".format(n_rules))
            break
    # Did not find the goal state :(
    return offers, finished, None
