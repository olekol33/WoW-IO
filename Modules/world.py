from __future__ import annotations

import os
import pandas as pd
from typing import MutableMapping, List

from Modules import *

# string to CityType
cities_types = {'capital': CityType.Capital, 'instance': CityType.Instance, 'major city': CityType.Major,
                'minor city': CityType.Minor}


class World:
    # initialize all continents (and the zones, and locations inside them), cities, and the zones-graph.
    def __init__(self):
        self._continents: MutableMapping[ContinentName, Continent] = {}
        self._zones: MutableMapping[str, Zone] = {}
        self._cities: List[City] = []
        self._named_cities: MutableMapping[str, City] = {}

        for continent_name in ContinentName:
            c = Continent(continent_name)
            self._continents[continent_name] = c
            self._zones.update(c.get_zones())

        # initialize all cities
        cities_df = pd.read_csv(os.path.join("Maps", f"cities.csv"), index_col='name', header=0)
        cities_df.dropna(inplace=True)
        int_fields = ['tl_x', 'tl_y']
        cities_df[int_fields] = cities_df[int_fields].astype(int)
        for _, city in cities_df.iterrows():
            zone = self._zones[city.zone]
            city_name = str(city.name)
            c = City(city_name, cities_types[city.type], (city.tl_x, city.tl_y), zone)
            self._cities.append(c)
            if city_name != 'NO NAME':
                self._named_cities[city_name] = c
            zone.add_city(c)
            for loc in c.get_locations():
                loc.set_city(c)

        # create neighbors graph
        with open(os.path.join('Maps', 'neighbors.txt'), 'r') as f:
            for line in f:
                if line.strip() != '' and line.strip()[0] != '#':
                    z = line.split(':')[0]
                    neighbors = line.split(':')[1]
                    for n in neighbors.split(','):
                        if n.strip():
                            self.get_zone(z.strip()).add_neighbor(self.get_zone(n.strip()))
        self._enforce_neighbors_bidirectionally()

    def reset(self) -> None:
        for cont in self._continents.values():
            cont.reset()

    def get_continent(self, continent_name: ContinentName) -> Continent:
        return self._continents[continent_name]

    def get_zones(self) -> MutableMapping[str, Zone]:
        return self._zones

    def is_zone(self, zone: str) -> bool:
        return zone in self._zones

    def get_zone(self, zone: str) -> Zone:
        return self._zones[zone]

    def get_place(self, place: str) -> Place:
        if self.is_zone(place):
            return self.get_zone(place)
        else:
            return self.get_city(place)

    def get_location(self, continent: Continent, x: int, y: int) -> Location:
        return self._continents[continent.get_name()].get_location(x, y)

    def is_city(self, city: str) -> bool:
        return city in self._named_cities

    def get_city(self, city: str) -> City:
        return self._named_cities[city]

    def get_named_cities(self) -> MutableMapping[str, City]:
        return self._named_cities

    def get_cities(self) -> List[City]:
        return self._cities

    def are_neighbors(self, z1: Zone, z2: Zone) -> bool:
        return z1.is_neighbor(z2)

    def _enforce_neighbors_bidirectionally(self):
        for z1 in self._zones.values():
            for z2 in z1.get_neighbors():
                assert z2.is_neighbor(z1), f'{z1} is not a neighbor of {z2}, but the opposite is true'

