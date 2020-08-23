import heapq

block_cost = 1
cost_weight = 0.5

def rule_search(start_state, rules, goal_state):
    offers = {}
    finished = set()
    h = [(0, start_state)]
    while len(h) != 0:
        priority, state = heapq.heappop(h)
        next_states = [(r, state.apply_rule(r)) for r in rules]
        for rule, (next_state, n_changed) in next_states:
            if next_state is not None:
                print("Applied rule: {}".format(rule.name))
                print(next_state.samus.position)
                # Mark it
                finished.add(next_state)
                offers[next_state] = state
                #TODO: requiring equality may be too much
                if next_state == goal_state:
                    return offers, finished, next_state
                distance = start_state.samus.position.euclidean(goal_state.samus.position)
                cost = block_cost * n_changed + rule.cost
                # Lower distance is good, lower cost is good
                priority = cost_weight * cost + (1 - cost_weight) * distance
                heapq.heappush((priority, n))
            else:
                print("Rule failed: {}".format(rule.name))
    # Did not find the goal state :(
    return offers, finished, None
