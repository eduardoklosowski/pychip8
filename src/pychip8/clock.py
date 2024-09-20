from time import monotonic_ns, sleep
from typing import Iterator, Protocol


class Tickable(Protocol):
    def tick(self) -> None:
        ...


def clock(tickable: Tickable, hz: int, /) -> Iterator[None]:
    time_clock = 1_000_000_000 / hz
    last = 0
    while True:
        now = monotonic_ns()
        time = last + time_clock - now
        if time > 0:
            sleep(time / 1_000_000_000)
            now = monotonic_ns()
        last = now

        tickable.tick()
        yield
