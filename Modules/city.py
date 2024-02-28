from __future__ import annotations

from enum import Enum
from typing import Tuple, Iterator
import random

from Modules import *
from conf import *


class CityType(Enum):
    Minor = (MINOR_CITY_WIDTH, MINOR_CITY_HEIGHT)
    Major = (MAJOR_CITY_WIDTH, MAJOR_CITY_HEIGHT)
    Capital = (CAPITAL_WIDTH, CAPITAL_HEIGHT)
    Instance = (INSTANCE_WIDTH, INSTANCE_HEIGHT)


class City(Place):
    def __init__(self, name: str, city_type: CityType, tl: Tuple[int, int], zone: Zone):
        self._zone = zone
        self._continent = zone.get_continent()
        self._city_type = city_type
        self._name = name
        self._tl = tl
        (_, (zone_br_x, zone_br_y)) = zone.get_bounds()
        tl_x, tl_y = tl
        self._br = (min(zone_br_x, tl_x+self._city_type.value[0]), min(zone_br_y, tl_y+self._city_type.value[1]))
        # the above _br is guaranteed not to collide with any other cities
        # (the tl was determined that way, in cities_build.py/random_coords()).

    def __str__(self) -> str:
        return f'City({self._name}, zone:{self._zone.get_name()}, (({self._tl[0]},{self._tl[1]}), ({self._br[0]},{self._br[1]})))'

    def get_name(self) -> str:
        return self._name

    def get_city_type(self) -> CityType:
        return self._city_type

    def get_zone(self) -> Zone:
        return self._zone

    def get_continent(self) -> Continent:
        return self._continent

    def get_bounds(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        return self._tl, self._br

    # iterator of all locations in this city.
    def get_locations(self) -> Iterator[Location]:
        for x in range(self._tl[0], self._br[0]):
            for y in range(self._tl[1], self._br[1]):
                yield self._continent.get_location(x, y)

    # get a random location inside this city.
    def get_random_location(self, prev_location: Location = None) -> Location:
        x = random.randint(self._tl[0], self._br[0] - 1)
        y = random.randint(self._tl[1], self._br[1] - 1)
        loc = self._continent.get_location(x, y)
        # assert loc.get_zone() == self.get_zone(), f'zone do not match {loc},  {loc.get_zone()}, {self.get_zone()}'
        # assert loc.get_city() == self, f'city do not match: {loc}\n {loc.get_city()}\n{self}'
        return loc
