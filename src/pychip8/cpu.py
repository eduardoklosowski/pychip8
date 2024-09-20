from typing import BinaryIO, Callable, List, Optional

from .core import Chip8Core
from .devices.devicebus import DeviceBus
from .devices.display import AddressableDisplay, Display
from .devices.keyboard import Keyboard
from .devices.ram import Ram
from .devices.rom import Rom


class Chip8:
    @classmethod
    def new_cosmac_vip_with_4096_ram(cls, *, instructions_per_update: int = 16) -> 'Chip8':  # pragma: no cover
        bus = DeviceBus()
        bus.map(0x000, Rom(size=512))
        bus.map(0x200, Ram(size=3328))
        display = Display(width=64, height=32)
        bus.map(0xf00, AddressableDisplay(display))
        keyboard = Keyboard()
        cores = [
            Chip8Core(
                bus=bus,
                reserved_address=352,
                display=display,
                keyboard=keyboard,
                entrypoint=0x200,
                instructions_per_update=instructions_per_update,
            ),
        ]
        return cls(
            cores=cores,
            bus=bus,
            display=display,
            keyboard=keyboard,
            instructions_per_update=instructions_per_update,
        )

    def __init__(
        self,
        *,
        cores: List[Chip8Core],
        bus: DeviceBus,
        display: Display,
        keyboard: Keyboard,
        instructions_per_update: int,
    ) -> None:
        self._cores = cores
        self._bus = bus
        self._display = display
        self._keyboard = keyboard
        self._instructions_per_update = instructions_per_update
        self._instructions_executable = 0
        self._tick_callback: Optional[Callable[[], None]] = None
        self._update_callback: Optional[Callable[[], None]] = None

    def __repr__(self) -> str:
        return f'Chip8(cores={len(self)})'

    def __len__(self) -> int:
        return len(self._cores)

    def load_program(self, program: BinaryIO, /, *, load_at: int = 0x200) -> None:
        self._bus.load_program(program, load_at)

    def set_tick_callback(self, callback: Optional[Callable[[], None]], /) -> None:
        self._tick_callback = callback

    def set_update_callback(self, callback: Optional[Callable[[], None]], /) -> None:
        self._update_callback = callback

    def tick(self) -> None:
        for core in self._cores:
            core.tick()
        if self._tick_callback:
            self._tick_callback()
        self._instructions_executable += 1
        if self._instructions_executable >= self._instructions_per_update:
            self._instructions_executable = 0
            if self._update_callback:
                self._update_callback()
