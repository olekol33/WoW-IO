from __future__ import annotations

from typing import Tuple, Iterator, List, Set, MutableMapping, Iterable
import random

from Modules import *
from conf import *


class Zone(Place):
    def __init__(self, name: str, continent: Continent, tl: Tuple[int, int], br: Tuple[int, int]):
        self._name: str = name
        self._tl: Tuple[int, int] = tl
        self._br: Tuple[int, int] = br
        self._continent: Continent = continent
        self._capitals: List[City] = []
        self._major_cities: List[City] = []
        self._minor_cities: List[City] = []
        self._instances: List[City] = []
        self._neighbors: MutableMapping[Zone, None] = {self: None}

    def __str__(self) -> str:
        return f'Zone({self._name}, (({self._tl[0]},{self._tl[1]}), ({self._br[0]},{self._br[1]})))'

    def get_name(self) -> str:
        return self._name

    # iterator of all locations in this zone.
    def get_locations(self) -> Iterator[Location]:
        for x in range(self._tl[0], self._br[0]):
            for y in range(self._tl[1], self._br[1]):
                yield self._continent.get_location(x, y)

    # add a city to this zone.
    def add_city(self, city) -> None:
        {
            CityType.Capital: self._capitals,
            CityType.Major: self._major_cities,
            CityType.Minor: self._minor_cities,
            CityType.Instance: self._instances,
        }[city.get_city_type()].append(city)

    def get_bounds(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        return self._tl, self._br

    def get_continent(self) -> Continent:
        return self._continent

    def add_neighbor(self, z: Zone) -> None:
        self._neighbors[z] = None

    def is_neighbor(self, z: Zone) -> bool:
        return z in self._neighbors

    def get_neighbors(self) -> Iterable[Zone]:
        return self._neighbors.keys()

    # get a random location in this zone - the end point of the 10-minute path that will be created,
    # starting from prev_location.
    def get_random_location(self, prev_location: Location = None) -> Location:
        if prev_location and prev_location.get_zone() == self and prev_location.is_city() and random.random() < P_SAME_CITY:
            loc = prev_location.get_city().get_random_location()

        elif len(self._capitals) > 0 and random.random() < P_CAPITAL:
            loc = random.choice(self._capitals).get_random_location()

        elif len(self._major_cities) > 0 and random.random() < P_MAJOR_CITY:
            loc = random.choice(self._major_cities).get_random_location()

        elif len(self._minor_cities) > 0 and random.random() < P_MINOR_CITY:
            loc = random.choice(self._minor_cities).get_random_location()

        elif len(self._instances) > 0 and random.random() < P_INSTANCE:
            loc = random.choice(self._instances).get_random_location()

        else:
            x = random.randint(self._tl[0], self._br[0]-1)
            y = random.randint(self._tl[1], self._br[1]-1)
            loc = self._continent.get_location(x, y)

        # assert loc.get_zone() == self, 'zone do not match'
        return loc
