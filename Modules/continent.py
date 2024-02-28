from __future__ import annotations

import os
from typing import Tuple, MutableMapping, List
from enum import Enum
import pandas as pd
import numpy as np

from Modules import *


# the continent enum (values are the continent names)
class ContinentName(Enum):
    Kalimdor = 'kalimdor'
    EasternKingdoms = 'eastern kingdoms'
    Outland = 'outland'


class Continent:
    # builds all of this-continent's zones (zones_df), locations, and the connections between them.
    def __init__(self, name: ContinentName):
        zones_df = pd.read_csv(os.path.join("Maps", f"{name.value}.csv"), index_col='name', header=0)
        zones_df.dropna(inplace=True)
        int_fields = ['tl_x', 'tl_y', 'br_x', 'br_y', 'capitals', 'major cities', 'minor cities']
        zones_df[int_fields] = zones_df[int_fields].astype(int)

        self._name: ContinentName = name
        self._zones: MutableMapping[str, zone.Zone] = {}

        self._br = (zones_df['br_x'].max(), zones_df['br_y'].max())
        self._locations = np.empty((self._br[1], self._br[0]), dtype=Location)

        # initialize locations (without a city/zone yet).
        for y in range(self._br[1]):
            for x in range(self._br[0]):
                self._locations[y][x] = Location(x, y, f'{name.value[0]}_{x}_{y}')

        # initialize all zones.
        for _, zone in zones_df.iterrows():
            z = Zone(zone.name, self, (zone.tl_x, zone.tl_y), (zone.br_x, zone.br_y))
            self._zones[zone.name] = z
            for loc in z.get_locations():
                loc.set_zone(z)

    def __str__(self) -> str:
        return f'Continent({self._name.value})'

    def reset(self):
        for x in range(self._br[0]):
            for y in range(self._br[1]):
                self.get_location(x, y).reset()

    def get_location(self, x, y) -> Location:
        return self._locations[y][x]

    def get_name(self) -> ContinentName:
        return self._name

    def get_bounds(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        return (0, 0), self._br

    def add_zone(self, zone: Zone) -> None:
        self._zones[zone.get_name()] = zone

    def is_zone(self, zone: str) -> bool:
        return zone in self._zones

    def get_zone(self, zone: str) -> Zone:
        return self._zones[zone]

    def get_zones(self) -> MutableMapping[str, Zone]:
        return self._zones
