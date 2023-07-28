import heapq

block_cost = 0
cost_weight = 0.5

def rule_search(start_state, rules, goal_state, max_rules=10000):
    if goal_state is None:
        goal_position = "None"
    else:
        goal_position = goal_state.position
    print("Search to reach {} from {}".format(goal_position, start_state.samus.position))
    offers = {}
    finished = set([start_state])
    entry_count = 0
    h = [(0, entry_count, start_state)]
    #TODO: is this the right thing to count / variable name?
    n_rules = 0
    while len(h) != 0:
        n_rules += 1
        #TODO: decreasekey!!
        # Use Heapdict
        priority, _, state = heapq.heappop(h)
        #if state in finished:
        #    continue
        #print("Was at: {}".format(state.samus))
        next_states = [(r, r.apply(state)) for r in rules]
        for rule, (next_state, err) in next_states:
            if next_state is not None:
                #print("\t{} applied at level {}".format(rule.name, n_rules))
                #print("\tNow at: {}".format(next_state.samus))
                #statestr = "{}_{}".format(n_rules, rule.name)
                #fname = "../output/rule_{}.png".format(statestr)
                #state_img = next_state.to_image()
                #state_img.save(fname)
                # Mark it
                #TODO: requiring equality may be too much
                # >=?
                # Found the goal state
                if goal_state is not None and next_state.samus == goal_state:
                    offers[next_state] = (rule, state)
                    finished.add(next_state)
                    return offers, finished, next_state
                if goal_state is not None:
                    distance = next_state.samus.position.euclidean(goal_state.position)
                else:
                    distance = 0
                #TODO
                #cost = block_cost * n_changed + rule.cost
                cost = rule.cost
                # Lower distance is good, lower cost is good
                priority = cost_weight * cost + (1 - cost_weight) * distance
                #print(n_changed)
                #print(distance)
                #print(priority)
                if next_state not in finished:
                    offers[next_state] = (rule, state)
                    finished.add(next_state)
                    heapq.heappush(h, (priority, entry_count, next_state))
                entry_count += 1
            else:
                pass
                #print("\t{} failed because {}".format(rule.name, err))
        if n_rules >= max_rules:
            print("Reached max rules!")
            break
    # Did not find the goal state :(
    print("Applied {} rules".format(n_rules))
    return offers, finished, None

def get_path(offers, start_state, goal_state):
    end_states = [o for o in offers if o.samus == goal_state]
    assert len(end_states) > 0, "Goal state not found!"
    current_state = end_states[0]
    rule_path = []
    state_path = [end_states[0]]
    while current_state.samus != start_state.samus:
        rule, prev_state = offers[current_state]
        rule_path.insert(0, rule)
        state_path.insert(0, prev_state)
        current_state = prev_state
    return rule_path, state_path
