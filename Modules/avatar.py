from __future__ import annotations

from typing import Deque, List, MutableMapping, Iterator, Optional
from collections import deque
import random

from Modules import *
from conf import include_writes


# An avatar holds its current location, next locations (_path and _place_changes),
# and its guild (_current_guild and _guild_changes)


class Avatar:
    def __init__(self, avatar_id: str, guilds_changes: Changes[Guild], places_changes: Changes[Place], world: World, debug: bool = False):
        self._world = world
        self._clock = -1
        self.id: str = f'AO_{avatar_id}'
        self._device_name: str = f'A_{avatar_id}'

        self._current_guild: Optional[Guild] = None
        self._guild_changes: Changes[Guild] = guilds_changes

        self._current_location: Optional[Location] = None
        self._place_changes: Changes[Place] = places_changes

        self._future_path: Deque[Location] = deque()   # queue of next locations.

        self.debug_path: List[Location] = []
        self._debug: bool = debug

        #for writes
        self.loc_updates: MutableMapping[int, Location] = {}
        self.guild_updates = []
        self._avatar_id = avatar_id

    def __str__(self) -> str:
        return f'Avatar(id: {self.id}, guild: {self._current_guild}, location: {self._current_location})'

    def clock(self) -> int:
        return self._clock

    # update guild. remove from last guild and insert to the new one.
    def _update_guild(self):
        assert (self._clock + 1) // SECONDS_IN_VTIME == self._guild_changes.vclock() + 1, f'{self.id}: guild changes clock is not synced'
        guild: Optional[Guild] = self._guild_changes.get_next_val()
        self.guild_updates.clear()

        if self._current_guild != guild:
            if self._current_guild is not None:
                self._current_guild.remove_avatar(self)
                self._update_guild_change()
            self._current_guild = guild
            if self._current_guild is not None:
                self._current_guild.add_avatar(self)
                self._update_guild_change()

    # set location. remove from last location and insert to the new one.
    def set_location(self, location: Optional[Location]):
        if self._current_location != location:
            if self._current_location is not None:
                self._current_location.remove_avatar(self)
            self._current_location = location
            if self._current_location is not None:
                self._current_location.add_avatar(self)
            # uncomment if a non-connected player shouldn't be read by its guild members.
            # else:
            #     self.set_guild(None)

    def get_id(self) -> str:
        return self.id

    def get_device_name(self) -> str:
        return self._device_name

    def get_guild(self) -> Optional[Guild]:
        return self._current_guild

    def get_location(self) -> Optional[Location]:
        return self._current_location

    # advance inner clock by 1 and set its location for the next one.
    # if no locations found in the _future_path, fill it with the update_future_path() call.
    def step(self) -> None:
        if not self._future_path:
            assert (self._clock + 1) % SECONDS_IN_VTIME == 0
            self._update_guild()
            self._update_future_path()

        self.set_location(self._future_path.popleft())
        self._clock += 1

    # iterator if all ios the player should read is this second.
    # itself, its location, the players in that locations, its guild and the guild members.
    def generate_io(self) -> Iterator[str]:
        loc = self.get_location()
        if not loc:
            return iter([])

        io_keys = set()
        io_keys.update(loc.get_avatars_dict().keys())
        io_keys.add(loc)

        guild = self.get_guild()
        if guild:
            io_keys.add(guild)
            io_keys.update(guild.get_avatars_dict().keys())

        io_keys = list(io_keys)
        ops = self._get_ops(io_keys)

        prefix = f'{self._device_name}, {self._clock}.0, '
        return (f'{prefix}{obj.id}, {ops[ind]}\n' for ind, obj in enumerate(io_keys))

    # build the future_path from current location to last_loc (random location from place,
    # taking into account your current location).
    # same spot for 10min if exact same location, manhattan route if neighbouring zones or same zone,
    # otherwise 5m here and 5m there (portal).
    # if became online this moment - will take a random route inside its starting place.
    def _update_future_path(self) -> None:
        assert (self._clock + 1) // SECONDS_IN_VTIME == self._place_changes.vclock() + 1, f'{self.id}: place changes clock is not synced'
        place = self._place_changes.get_next_val()
        self.loc_updates.clear()
        if place is None:
            self._future_path = deque([None] * SECONDS_IN_VTIME)
        else:
            if not self._current_location:
                # was offline
                self.set_location(place.get_random_location(self._current_location))

            last_loc = place.get_random_location(self._current_location)

            if self._current_location == last_loc:
                # stayed in same location
                self._future_path = deque([last_loc] * SECONDS_IN_VTIME)

            elif not self._current_location.get_zone().is_neighbor(last_loc.get_zone()):
                # do not have a common border - used portal
                # self._future_path.extend([self._current_location] * (SECONDS_IN_VTIME // 2))
                # self._future_path.extend([last_loc] * (SECONDS_IN_VTIME // 2))
                self._extend_future_path(self._current_location, SECONDS_IN_VTIME // 2, SECONDS_IN_VTIME)
                self._extend_future_path(last_loc, SECONDS_IN_VTIME // 2, SECONDS_IN_VTIME // 2)
            else:
                change_time = 0
                remaining_time = SECONDS_IN_VTIME
                if self._current_location.is_city():
                    # self._future_path.extend([self._current_location] * (3 * MINUTE))
                    self._extend_future_path(self._current_location, 3 * MINUTE, remaining_time)
                    remaining_time -= 3 * MINUTE

                manhattan_dist, horizontals, verticals = self._current_location.manhattan_to(last_loc)
                seconds_for_loc = remaining_time // manhattan_dist
                # assert seconds_for_loc > 0, f'{self.id}: in time {self.clock()}: seconds_for_loc: {seconds_for_loc}'

                x, y = self._current_location.get_coords()
                cont = self._current_location.get_continent()

                while horizontals or verticals:
                    if not horizontals or verticals and random.random() <= 0.5:
                        y = verticals.popleft()
                    else:
                        x = horizontals.popleft()
                    # print(f'({x}, {y})', end='->')
                    self._extend_future_path(self._world.get_location(cont, x, y), seconds_for_loc, remaining_time)
                    remaining_time -= seconds_for_loc
                    # change_time += seconds_for_loc

                self._future_path.extend([self._world.get_location(cont, x, y)] * remaining_time)
                # self._extend_future_path(self._world.get_location(cont, x, y), remaining_time, remaining_time)

        # assert len(self._future_path) == SECONDS_IN_VTIME, f'path length not valid: {len(self._future_path)}'
        if self._debug:
            self.debug_path.extend(self._future_path)

    # return "WRITE" if it's an object generated by this avatar
    #object_name is of format AO_<avatar_id> and avatar name is of format A_<avatar_id>
    def _get_ops(self, io_keys) -> []:
        ops = ["READ"] * len(io_keys)
        if not include_writes:
            return ops
        for ind, obj in enumerate(io_keys):
            if obj.id == f'AO_{self._avatar_id}':
                ops[ind] = "WRITE"
                break
        return ops

    def get_loc_updates(self) -> MutableMapping[int, Location]:
        return self.loc_updates

    def _extend_future_path(self, loc: Location, seconds_for_loc: int, remaining_time: int) -> None:
        self.loc_updates[SECONDS_IN_VTIME - remaining_time] = loc
        self._future_path.extend([loc] * seconds_for_loc)

    def _update_guild_change(self) -> None:
        self.guild_updates.append(self._current_guild)

