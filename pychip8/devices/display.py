from typing import Callable, List, Optional


class Display:
    def __init__(self, *, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self._frame = [[False for _ in range(width)] for _ in range(height)]
        self._clear_callback: Optional[Callable[[], None]] = None
        self._update_pixel_callback: Optional[Callable[[int, int, bool], None]] = None

    def __repr__(self) -> str:
        return f'Display({self.width}x{self.height})'

    def __str__(self) -> str:
        return '\n'.join(
            ''.join(
                '\u2588' if pixel else ' '
                for pixel in line
            )
            for line in self._frame
        )

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
        return flipped  # noqa: R504

    def draw_sprite(self, x: int, y: int, sprite: List[int], /) -> bool:
        flipped = False
        for y2, line in enumerate(sprite):
            for x2 in range(8):
                pixel = bool(line >> (7 - x2) & 1)
                if pixel and self.set_pixel(x + x2, y + y2, pixel):
                    flipped = True
        return flipped

    def set_clear_callback(self, callback: Optional[Callable[[], None]], /) -> None:
        self._clear_callback = callback

    def set_update_pixel_callback(self, callback: Optional[Callable[[int, int, bool], None]], /) -> None:
        self._update_pixel_callback = callback
