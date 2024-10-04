from collections.abc import Callable
from math import ceil


class Display:
    PIXEL_ON = '\u2588'
    PIXEL_OFF = ' '

    def __init__(self, *, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self._frame = [[False for _ in range(width)] for _ in range(height)]
        self._clear_callback: Callable[[], None] | None = None
        self._update_pixel_callback: Callable[[int, int, bool], None] | None = None

    def __repr__(self) -> str:
        return f'Display({self.width}x{self.height})'

    def __str__(self) -> str:
        return '\n'.join(''.join(self.PIXEL_ON if pixel else self.PIXEL_OFF for pixel in line) for line in self._frame)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def clear(self) -> None:
        self._frame = [[False for _ in range(self.width)] for _ in range(self.height)]
        if self._clear_callback:
            self._clear_callback()

    def refresh(self) -> None:
        if self._update_pixel_callback:
            for y in range(self.height):
                for x in range(self.width):
                    self._update_pixel_callback(x, y, self._frame[y][x])

    def get_pixel(self, x: int, y: int, /) -> bool:
        x %= self.width
        y %= self.height
        return self._frame[y][x]

    def set_pixel(self, x: int, y: int, value: bool, /) -> bool:
        x %= self.width
        y %= self.height
        flipped = False
        if value and self._frame[y][x]:
            flipped = True
            value = False
        self._frame[y][x] = value
        if self._update_pixel_callback:
            self._update_pixel_callback(x, y, value)
        return flipped

    def draw_sprite(self, x: int, y: int, sprite: list[int], /) -> bool:
        flipped = False
        for y2, line in enumerate(sprite):
            for x2 in range(8):
                pixel = bool(line >> (7 - x2) & 1)
                if pixel and self.set_pixel(x + x2, y + y2, pixel):
                    flipped = True
        return flipped

    def set_clear_callback(self, callback: Callable[[], None] | None, /) -> None:
        self._clear_callback = callback

    def set_update_pixel_callback(self, callback: Callable[[int, int, bool], None] | None, /) -> None:
        self._update_pixel_callback = callback


class AddressableDisplay:
    def __init__(self, display: Display, /) -> None:
        self._display = display

    def __repr__(self) -> str:
        return f'AddressableDisplay({self._display!r})'

    def __len__(self) -> int:
        return ceil(self._display.width * self._display.height / 8)

    def _calc_pixel_position(self, pixel_number: int, /) -> tuple[int, int]:
        return pixel_number % self._display.width, pixel_number // self._display.width

    def __getitem__(self, address: int, /) -> int:
        value = 0
        for pixel_number in range(address * 8, (address + 1) * 8):
            value = (value << 1) | self._display.get_pixel(*self._calc_pixel_position(pixel_number))
        return value

    def __setitem__(self, address: int, value: int, /) -> None:
        for i, pixel_number in enumerate(range(address * 8, (address + 1) * 8)):
            self._display.set_pixel(*self._calc_pixel_position(pixel_number), bool(value >> (7 - i) & 1))
