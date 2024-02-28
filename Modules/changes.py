from collections import deque
from typing import Deque, Tuple, Generic, TypeVar, Optional

MINUTE = 60
MINUTES_IN_VTIME = 10
SECONDS_IN_VTIME = MINUTES_IN_VTIME * MINUTE
T = TypeVar('T')


# The idea here is a queue of (vtime, values) - describes the changes in some variable over time.
# used for guild, locations.


class Changes(Generic[T]):
    def __init__(self, avatar_id: str, init_val: Optional[T] = None):
        self._avatar_id: str = avatar_id
        self._cur_val: Optional[T] = init_val
        self._vclock: int = -1
        self._last_change_time: int = -1
        self._last_change_val: Optional[T] = init_val
        self._changes: Deque[Tuple[int, Optional[T]]] = deque()
        self._lock_changes: bool = False

    def __str__(self) -> str:
        changes = ', '.join(f'{t}: {v}' for t, v in self._changes)
        return f'Changes(avatar: {self._avatar_id}, [{changes}])'

    # increment the inner-clock, and get the current value (will be at the top of the queue, maybe after 1 pop()).
    def get_next_val(self) -> Optional[T]:
        self._lock_changes = True
        self._vclock += 1

        if self._changes:
            # assert self._changes[0][0] >= self._vclock, f'{self._avatar_id}: clock {self._vclock} skipped the next change {self._changes[0][0]}'
            if self._changes[0][0] == self._vclock:
                self._cur_val = self._changes.popleft()[1]
        return self._cur_val

    # register a new change (time must be >= from the last time entered, will be inserted at the end of the queue).
    def register_change(self, vtime: int, val: Optional[T]) -> None:
        assert not self._lock_changes, f'{self._avatar_id}: cant register change after lock'
        assert vtime >= self._last_change_time, f'{self._avatar_id}: cant register change before last change time (reg:{vtime}, last:{self._last_change_time})'
        # assert vtime != self._last_change_time or self._last_change_val == val, f'{self._avatar_id} DOUBLE REGISTER OF THE SAME TIME ({self._last_change_val}->{val})'
        if vtime == self._last_change_time and self._last_change_val != val:
            return   #avoid more than one change in vtime
        self._last_change_time = vtime
        if val != self._last_change_val:
            self._changes.append((vtime, val))
            self._last_change_val = val

    def vclock(self) -> int:
        return self._vclock
