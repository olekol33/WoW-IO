from __future__ import annotations

from collections import deque
from typing import MutableMapping, AbstractSet, Tuple, Deque

from Modules import *


# The Location role is to know which avatars are in it at all times (like a Set[Avatar]).
# Also - it knows in which zone and city it's found (_city=None for no city).


class Location:
    def __init__(self, x: int, y: int, location_id: str):
        self.id: str = f'LO_{location_id}'
        self._x = x
        self._y = y
        self._zone = None
        self._city = None
        self._avatars: MutableMapping[Avatar, None] = dict()

    def __str__(self) -> str:
        avatars_ids = ','.join(a.get_id() for a in self._avatars)
        return f'Location({self._zone.get_continent()} ({self._x},{self._y}), avatars: [{avatars_ids}])'

    def get_id(self):
        return self.id

    def reset(self) -> None:
        self._avatars.clear()

    def set_city(self, city) -> None:
        self._city = city

    def set_zone(self, zone) -> None:
        self._zone = zone

    def get_coords(self) -> (int, int):
        return self._x, self._y

    def is_city(self) -> bool:
        return self._city is not None

    def get_city(self) -> City:
        return self._city

    def get_zone(self) -> Zone:
        return self._zone

    def get_continent(self) -> Continent:
        return self._zone.get_continent()

    def get_avatars(self) -> AbstractSet[Avatar]:
        # assert all(a.get_location() == self for a in self._avatars)   # uncomment for sanity checks.
        return self._avatars.keys()

    def get_avatars_dict(self) -> MutableMapping[Avatar, None]:
        return self._avatars

    def get_num_avatars(self) -> int:
        return len(self._avatars)

    def add_avatar(self, avatar: Avatar) -> None:
        self._avatars[avatar] = None

    def remove_avatar(self, avatar: Avatar) -> None:
        del self._avatars[avatar]

    # return (total_dist, horizontal_queue, vertical_queue),
    #  such that each queue holds the next values to be used if the avatar will go in that direction
    #  (ordered from first to last).
    # for example (0,2)->(4,4) will return (6, queue(1,2,3,4), queue(3,4)).
    def manhattan_to(self, next_loc: Location) -> Tuple[int, Deque[int], Deque[int]]:
        assert self.get_continent() == next_loc.get_continent(), f'{self} and {next_loc} are not in the same continent'
        cur_x, cur_y = self.get_coords()
        next_x, next_y = next_loc.get_coords()

        h_dist = abs(next_x - cur_x)
        v_dist = abs(next_y - cur_y)

        # h_step = max((h_dist - 1) // SECONDS_IN_VTIME + 1, 1)
        # v_step = max((v_dist - 1) // SECONDS_IN_VTIME + 1, 1)
        # assert h_step == 1
        # assert v_step == 1
        h_step = 1
        v_step = 1
        assert h_dist + v_dist <= SECONDS_IN_VTIME, f'manhattan distance between {self} and {next_loc} is too big: {h_dist + v_dist}'

        horizontals = deque(range(cur_x+h_step, next_x+1, h_step) if cur_x <= next_x else range(cur_x-h_step, next_x-1, -h_step))
        verticals = deque(range(cur_y+v_step, next_y+1, v_step) if cur_y <= next_y else range(cur_y-v_step, next_y-1, -v_step))
        # assert h_dist + v_dist == len(horizontals) + len(verticals)
        return h_dist + v_dist, horizontals, verticals
