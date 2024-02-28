from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator, Tuple

from Modules import *


# An abstract class that zone and city inherit from (has a name, bounds, continent, locations iterator,
#  and a random location function).


class Place(ABC):

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_bounds(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        pass

    @abstractmethod
    def get_continent(self) -> Continent:
        pass

    @abstractmethod
    def get_locations(self) -> Iterator[Location]:
        pass

    @abstractmethod
    def get_random_location(self, prev_location: Location) -> Location:
        pass
