import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Final

import sdl2
import sdl2.ext

from pychip8.clock import clock
from pychip8.cpu import Chip8
from pychip8.devices.keyboard import Key


@contextmanager
def sdl_environment() -> Iterator[None]:
    sdl2.ext.init()
    yield
    sdl2.ext.quit()


class Window:
    BLACK_PIXEL: Final = sdl2.ext.Color(0, 0, 0)
    WHITE_PIXEL: Final = sdl2.ext.Color(255, 255, 255)
    KEYS: Final = {
        sdl2.SDLK_1: Key.KEY1,
        sdl2.SDLK_2: Key.KEY2,
        sdl2.SDLK_3: Key.KEY3,
        sdl2.SDLK_q: Key.KEY4,
        sdl2.SDLK_w: Key.KEY5,
        sdl2.SDLK_e: Key.KEY6,
        sdl2.SDLK_a: Key.KEY7,
        sdl2.SDLK_s: Key.KEY8,
        sdl2.SDLK_d: Key.KEY9,
        sdl2.SDLK_x: Key.KEY0,
        sdl2.SDLK_z: Key.KEYA,
        sdl2.SDLK_c: Key.KEYB,
        sdl2.SDLK_4: Key.KEYC,
        sdl2.SDLK_r: Key.KEYD,
        sdl2.SDLK_f: Key.KEYE,
        sdl2.SDLK_v: Key.KEYF,
    }

    def __init__(self, *, cpu: Chip8, size: tuple[int, int]) -> None:
        self._cpu = cpu
        self._display = cpu.display
        self._keyboard = cpu.keyboard

        self._window = sdl2.ext.Window('PyChip8', size=size)
        self._window.show()
        self._render = sdl2.ext.Renderer(self._window, logical_size=(self._display.width, self._display.height))
        self._render.clear(self.BLACK_PIXEL)
        self._render.present()

        self._need_update = False
        self._frame = [[False for _ in range(self._display.width)] for _ in range(self._display.height)]

        self._display.set_update_pixel_callback(self.set_pixel)
        self._display.set_clear_callback(self.clear)
        self._cpu.set_update_callback(self.show_frame)

    def close(self) -> None:
        self._display.set_update_pixel_callback(None)
        self._display.set_clear_callback(None)
        self._cpu.set_update_callback(None)
        self._render.destroy()
        self._window.close()

    def clear(self) -> None:
        self._frame = [[False for _ in range(self._display.width)] for _ in range(self._display.height)]
        self._need_update = True

    def set_pixel(self, x: int, y: int, value: bool, /) -> None:
        self._frame[y][x] = value
        self._need_update = True

    def show_frame(self) -> None:
        if self._need_update:
            self._need_update = False
            for y, line in enumerate(self._frame):
                for x, pixel in enumerate(line):
                    self._render.draw_point((x, y), self.WHITE_PIXEL if pixel else self.BLACK_PIXEL)
            self._render.present()

    def run(self, hz: int, /) -> None:
        cpu_clock = clock(self._cpu, hz)
        running = True
        while running:
            next(cpu_clock)
            for event in sdl2.ext.get_events():
                if event.type == sdl2.SDL_QUIT or (
                    event.type == sdl2.SDL_KEYDOWN and event.key.keysym.sym == sdl2.SDLK_ESCAPE
                ):
                    running = False
                    break
                if event.type in (sdl2.SDL_KEYDOWN, sdl2.SDL_KEYUP):
                    key = self.KEYS.get(event.key.keysym.sym)
                    if key is not None:
                        self._keyboard[key] = event.type == sdl2.SDL_KEYDOWN
        self.close()


def main(
    *,
    program: BinaryIO,
    instructions_per_update: int = 16,
    clock: int = 960,
    size: tuple[int, int] = (800, 400),
) -> None:
    with sdl_environment():
        cpu = Chip8.new_cosmac_vip_with_4096_ram(instructions_per_update=instructions_per_update)
        cpu.load_program(program)
        window = Window(cpu=cpu, size=size)
        window.run(clock)


if __name__ == '__main__':
    with Path(sys.argv[1]).open('rb') as f:
        main(program=f)
