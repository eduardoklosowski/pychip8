from asyncio import CancelledError, InvalidStateError
from enum import IntEnum, auto
from typing import Generic, TypeVar

T = TypeVar('T')


class Future(Generic[T]):
    def __init__(self) -> None:
        self._result: T | None = None
        self._cancelled = False

    def done(self) -> bool:
        return self._result is not None

    def cancel(self) -> bool:
        if not self._cancelled and self._result is None:
            self._cancelled = True
            return True
        return False

    def cancelled(self) -> bool:
        return self._cancelled

    def set_result(self, result: T) -> None:
        if self._cancelled or self._result is not None:
            raise InvalidStateError
        self._result = result

    def result(self) -> T:
        if self._cancelled:
            raise CancelledError
        if self._result is None:
            raise InvalidStateError
        return self._result


class Key(IntEnum):
    KEY0 = 0
    KEY1 = auto()
    KEY2 = auto()
    KEY3 = auto()
    KEY4 = auto()
    KEY5 = auto()
    KEY6 = auto()
    KEY7 = auto()
    KEY8 = auto()
    KEY9 = auto()
    KEYA = auto()
    KEYB = auto()
    KEYC = auto()
    KEYD = auto()
    KEYE = auto()
    KEYF = auto()


class Keyboard:
    def __init__(self) -> None:
        self._pressed = [False for _ in range(len(Key))]
        self._notify_pressed: list[Future[Key]] = []

    def __repr__(self) -> str:
        keys = ', '.join(
            f'{key.name.removeprefix("KEY")}' for key, value in zip(Key, self._pressed, strict=True) if value
        )
        return f'Keyboard(pressed="{keys}")'

    def __len__(self) -> int:
        return len(self._pressed)

    def __getitem__(self, key: Key, /) -> bool:
        return self._pressed[key]

    def __setitem__(self, key: Key, value: bool, /) -> None:
        self._pressed[key] = value
        if value:
            while self._notify_pressed:
                future = self._notify_pressed.pop()
                if not future.cancelled():
                    future.set_result(key)

    def next_key_pressed(self) -> Future[Key]:
        future: Future[Key] = Future()
        self._notify_pressed.append(future)
        return future
