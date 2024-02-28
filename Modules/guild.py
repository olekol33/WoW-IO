from __future__ import annotations

from typing import MutableMapping, AbstractSet

from Modules import *


# The Guild role is to know which avatars are in it at all times (like a Set[Avatar]).


class Guild:
    def __init__(self, guild_id: str):
        self.id: str = f'GO_{guild_id}'
        self._avatars: MutableMapping[Avatar, None] = dict()

    def __str__(self) -> str:
        avatars_ids = ','.join(a.get_id() for a in self._avatars)
        return f'Guild(id: {self.id}, avatars_ids: [{avatars_ids}])'

    def add_avatar(self, avatar: Avatar) -> None:
        self._avatars[avatar] = None

    def remove_avatar(self, avatar: Avatar) -> None:
        del self._avatars[avatar]

    def get_id(self) -> str:
        return self.id

    def get_avatars(self) -> AbstractSet[Avatar]:
        # assert all(a.get_guild() == self for a in self._avatars)  # uncomment for sanity checks.
        return self._avatars.keys()

    def get_avatars_dict(self) -> MutableMapping[Avatar]:
        return self._avatars
