# Map Actions are a new way to generate the map.
# During generation, we keep track of a MapState and PlayerState
# A MapState consists of:
#   - a single CMap
#   - information about where the (overlapping) regions are on that CMap.
#   - information about where rules have been applied
# A PlayerState consists of:
#   - a position on the CMap
#   - a region
#   - an ItemSet

# A MapAction consists of:
#   - a list of available regions
#   - a ConstraintGraph (may be elided for simple rules)
#   - a partial mapping from ConstraintGraph nodes to relative locations
#   - a function that edits the CMap
#   - a cost function
#   - a list of partial or complete room definitions that accompany the MapAction

# Generation consists of applying a series of MapActions
# Some MapActions may be very low-cost movements that do not edit the map (e.g. backtracking through a room)
# When applying the MapAction, the nodes of the ConstraintGraph get attached to particular locations in the CMap
# At a given location, the player can:
#   - Travel through one of the CGraphs attached to this node, to any of the reachable nodes
#       - Paying a cost proportional to the physical distance traveled
#   - Apply a new MapAction to travel to any of the reachable nodes
#       - The new MapAction must be compatible with the current PlayerState, and move the player to a new location
#       - The new MapAction must be compatible with the current CMap (not overwrite any locations)
#TODO: how to decide whether a MapAction overwrites something? Sometimes, tiles can be legitimately overlapping

# Generation strategies can be advanced (e.g. keeping track of how many rules are applied, the last item that the player acquired, etc.
# This can apply a cost function over some kind of generation state to determine when to apply rules
# For example, a rule with a CGraph that includes a constraint on a certain item should be more likely to be applied immediately after obtaining that item
# Generation can be done via search over GenerationStates, with MapActions as the edges in that space.
# A pruning strategy can be used to ensure the search space does not grow too large
# This search could either be a global search for a valid configuration,
# or a local search to instantiate each edge of the Abstract Map, as is the case now.
#   - In this case, A* search can minimize the total cost of MapActions applied, plus some estimate of cost-to-go, like Manhattan Distance to the goal node

# CMap tiles are also labeled with what region they belong to, and MapActions can edit this mapping
# For example, placing an elevator places some MapTiles, as well as editing the region info for those tiles, and changing the PlayerState's region
# Could include multiple Elevator rules that make longer elevators at a reduced cost.

# Cost to apply a rule could depend on the MapTiles present. For example, coercing a blank tile costs more than coercing a tile that is in use, but has a wall at the required location.
#TODO: How to do tile coercion? How to know what walls a MapAction will destroy?
