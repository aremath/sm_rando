import heapq

block_cost = 0
cost_weight = 0.5
max_rules = 60

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
        #if state in finished:
        #    continue
        print("Was at: {}|{}".format(state.samus.position, state.samus.pose))
        next_states = [(r, r.apply(state)) for r in rules]
        for rule, (next_state, err) in next_states:
            if next_state is not None:
                print("Applied rule: {} at level {}".format(rule.name, n_rules))
                print("Now at: {}|{}".format(next_state.samus.position, next_state.samus.pose))
                statestr = "{}_{}".format(n_rules, rule.name)
                fname = "../output/rule_{}.png".format(statestr)
                state_img = next_state.to_image()
                state_img.save(fname)
                # Mark it
                offers[next_state] = state
                #TODO: requiring equality may be too much
                # >=?
                if next_state.samus == goal_state:
                    return offers, finished, next_state
                distance = next_state.samus.position.euclidean(goal_state.position)
                #TODO
                #cost = block_cost * n_changed + rule.cost
                cost = rule.cost
                # Lower distance is good, lower cost is good
                priority = cost_weight * cost + (1 - cost_weight) * distance
                #print(n_changed)
                #print(distance)
                #print(priority)
                if next_state not in finished:
                    finished.add(next_state)
                    heapq.heappush(h, (priority, entry_count, next_state))
                entry_count += 1
            else:
                print("Rule failed: {}".format(rule.name))
                print("Because: {}".format(err))
        if n_rules >= max_rules:
            print("Reached max rules!")
            break
    # Did not find the goal state :(
    print("Applied {} rules".format(n_rules))
    return offers, finished, None
