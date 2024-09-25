import curses
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Final

from pychip8.clock import clock
from pychip8.cpu import Chip8
from pychip8.devices.keyboard import Key


@contextmanager
def ncurses_environment() -> Iterator['curses._CursesWindow']:
    stdscr = None
    try:
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        stdscr.keypad(True)
        stdscr.nodelay(True)
        yield stdscr
    finally:
        if stdscr is not None:
            stdscr.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        curses.curs_set(1)


class Window:
    BLACK_PIXEL: Final = ' '
    WHITE_PIXEL: Final = '\u2588'
    KEYS: Final = {
        '1': Key.KEY1,
        '2': Key.KEY2,
        '3': Key.KEY3,
        'q': Key.KEY4,
        'w': Key.KEY5,
        'e': Key.KEY6,
        'a': Key.KEY7,
        's': Key.KEY8,
        'd': Key.KEY9,
        'x': Key.KEY0,
        'z': Key.KEYA,
        'c': Key.KEYB,
        '4': Key.KEYC,
        'r': Key.KEYD,
        'f': Key.KEYE,
        'v': Key.KEYF,
    }

    def __init__(self, *, scr: 'curses._CursesWindow', cpu: Chip8) -> None:
        self._scr = scr
        self._cpu = cpu
        self._display = cpu.display
        self._keyboard = cpu.keyboard

        columns, lines = os.get_terminal_size()
        if columns < self._display.width or lines < self._display.height + 1:
            raise RuntimeError(
                f'Small terminal ({columns}x{lines}), minimum {self._display.width}x{self._display.height + 1}',
            )

        self._display.set_update_pixel_callback(self.set_pixel)
        self._display.set_clear_callback(self.clear)

    def close(self) -> None:
        self._display.set_update_pixel_callback(None)
        self._display.set_clear_callback(None)

    def clear(self) -> None:
        self._scr.clear()

    def set_pixel(self, x: int, y: int, value: bool, /) -> None:
        self._scr.move(y, x)
        self._scr.addch(self.WHITE_PIXEL if value else self.BLACK_PIXEL)

    def run(self, hz: int, /) -> None:
        cpu_clock = clock(self._cpu, hz)
        running = True
        while running:
            next(cpu_clock)
            for key in Key:
                self._keyboard[key] = False
            try:
                char = self._scr.getkey()
                if char == '\x1b':
                    running = False
                    break
                key_pressed = self.KEYS.get(char)
                if key_pressed:
                    self._keyboard[key_pressed] = True
            except curses.error:
                ...
        self.close()


def main(
    *,
    program: BinaryIO,
    instructions_per_update: int = 16,
    clock: int = 960,
    size: tuple[int, int] = (0, 0),  # noqa: ARG001
) -> None:
    with ncurses_environment() as stdscr:
        cpu = Chip8.new_cosmac_vip_with_4096_ram(instructions_per_update=instructions_per_update)
        cpu.load_program(program)
        window = Window(scr=stdscr, cpu=cpu)
        window.run(clock)


if __name__ == '__main__':
    with Path(sys.argv[1]).open('rb') as f:
        main(program=f)
