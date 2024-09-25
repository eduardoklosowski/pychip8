from argparse import ArgumentParser
from importlib import import_module
from pathlib import Path


def parse_size(value: str) -> tuple[int, int]:
    width, height = value.split('x')
    return int(width), int(height)


parser = ArgumentParser(
    prog='pychip8',
    description='Chip-8 emulator written in Python',
)
parser.add_argument(
    'file',
    help='path of the ROM to be executed',
)
parser.add_argument(
    '-c',
    '--clock',
    type=int,
    default=960,
    help='clock of CPU in Hertz (default: 960)',
)
parser.add_argument(
    '-i',
    '--instructions_per_update',
    type=int,
    default=16,
    help='number of instructions executed in an update (default: 16)',
)
parser.add_argument(
    '--interface',
    metavar='INTERFACE',
    choices=['ncurses', 'sdl'],
    default='ncurses',
    help='select interface (default: ncurses)',
)
parser.add_argument(
    '--ncurses',
    dest='interface',
    action='store_const',
    const='ncurses',
    help='use ncurses interface',
)
parser.add_argument(
    '--sdl',
    dest='interface',
    action='store_const',
    const='sdl',
    help='use SDL interface',
)
parser.add_argument(
    '-s',
    '--size',
    type=parse_size,
    default=(800, 400),
    help='size for GUI window (default: 800x400)',
)


def main() -> None:
    try:
        args = parser.parse_args()
        with Path(args.file).open('rb') as f:
            import_module(f'.{args.interface}', 'pychip8.interface').main(
                program=f,
                instructions_per_update=args.instructions_per_update,
                clock=args.clock,
                size=args.size,
            )
    except KeyboardInterrupt:
        ...


if __name__ == '__main__':
    main()
