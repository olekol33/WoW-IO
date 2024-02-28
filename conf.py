
# The probabilities defined in the word doc - defining where is next location (10 minutes ahead) will be.
P_SAME_CITY = 0.5       # should the player stay in its current city.
P_CAPITAL = 0.2         # should the player go to some capital in this zone.
P_INSTANCE = 0.3        # should the player go to some instance in this zone.
P_MAJOR_CITY = 0.15     # should the player go to some major city in this zone.
P_MINOR_CITY = 0.03     # should the player go to some minor city in this zone.


# city/instance size (width, height) in 60*60 meters blocks.
CAPITAL_WIDTH = 3
CAPITAL_HEIGHT = 3

MAJOR_CITY_WIDTH = 2
MAJOR_CITY_HEIGHT = 2

MINOR_CITY_WIDTH = 1
MINOR_CITY_HEIGHT = 1

INSTANCE_WIDTH = 2
INSTANCE_HEIGHT = 2

# writes
include_writes = True
