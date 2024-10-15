from collections.abc import Callable
from io import BytesIO
from random import randint
from typing import cast
from unittest.mock import MagicMock

from pychip8.core import Chip8Core
from pychip8.cpu import Chip8
from pychip8.devices.devicebus import DeviceBus
from pychip8.devices.display import Display
from pychip8.devices.keyboard import Keyboard


class TestChip8:
    def test_repr(self) -> None:
        for i in range(10):
            sut = Chip8(
                cores=[MagicMock(spec_set=Chip8Core) for _ in range(i)],
                bus=MagicMock(spec_set=DeviceBus),
                display=MagicMock(spec_set=Display),
                keyboard=MagicMock(spec_set=Keyboard),
                instructions_per_update=16,
            )

            assert repr(sut) == f'Chip8(cores={i})'

    def test_length(self) -> None:
        for i in range(10):
            sut = Chip8(
                cores=[MagicMock(spec_set=Chip8Core) for _ in range(i)],
                bus=MagicMock(spec_set=DeviceBus),
                display=MagicMock(spec_set=Display),
                keyboard=MagicMock(spec_set=Keyboard),
                instructions_per_update=16,
            )

            assert len(sut) == i

    def test_load_program(self) -> None:
        for _ in range(10):
            content = [randint(0, 255) for _ in range(randint(1, 512))]
            program = BytesIO(bytes(content))

            mock_bus = MagicMock(spec_set=DeviceBus)

            sut = Chip8(
                cores=[MagicMock(spec_set=Chip8Core)],
                bus=mock_bus,
                display=MagicMock(spec_set=Display),
                keyboard=MagicMock(spec_set=Keyboard),
                instructions_per_update=16,
            )

            sut.load_program(program)

            mock_bus.load_program.assert_called_once_with(program, 0x200)

    def test_load_program_with_load_at(self) -> None:
        for _ in range(10):
            address = randint(0, 2048)
            content = [randint(0, 255) for _ in range(randint(1, 512))]
            program = BytesIO(bytes(content))

            mock_bus = MagicMock(spec_set=DeviceBus)

            sut = Chip8(
                cores=[MagicMock(spec_set=Chip8Core)],
                bus=mock_bus,
                display=MagicMock(spec_set=Display),
                keyboard=MagicMock(spec_set=Keyboard),
                instructions_per_update=16,
            )

            sut.load_program(program, load_at=address)

            mock_bus.load_program.assert_called_once_with(program, address)

    def test_tick(self) -> None:
        for i in range(10):
            instructions_per_update = randint(1, 16)
            cores = [MagicMock(spec_set=Chip8Core) for _ in range(i)]

            sut = Chip8(
                cores=cast(list[Chip8Core], cores),
                bus=MagicMock(spec_set=DeviceBus),
                display=MagicMock(spec_set=Display),
                keyboard=MagicMock(spec_set=Keyboard),
                instructions_per_update=16,
            )

            for j in range(1, instructions_per_update * 3 + 1):
                sut.tick()

                for core in cores:
                    assert core.tick.call_count == j

    def test_callbacks_in_tick(self) -> None:
        for i in range(10):
            instructions_per_update = randint(1, 16)
            cores = [MagicMock(spec_set=Chip8Core) for _ in range(i)]

            tick_callback = MagicMock(spec_set=Callable)
            update_callback = MagicMock(spec_set=Callable)

            sut = Chip8(
                cores=cast(list[Chip8Core], cores),
                bus=MagicMock(spec_set=DeviceBus),
                display=MagicMock(spec_set=Display),
                keyboard=MagicMock(spec_set=Keyboard),
                instructions_per_update=instructions_per_update,
            )
            sut.set_tick_callback(tick_callback)
            sut.set_update_callback(update_callback)

            for j in range(1, instructions_per_update * 3 + 1):
                sut.tick()

                assert tick_callback.call_count == j
                assert update_callback.call_count == j // instructions_per_update

    def test_display(self) -> None:
        mock_display = MagicMock(spec_set=Display)

        sut = Chip8(
            cores=[MagicMock(spec_set=Chip8Core)],
            bus=MagicMock(spec_set=DeviceBus),
            display=mock_display,
            keyboard=MagicMock(spec_set=Keyboard),
            instructions_per_update=16,
        )

        assert sut.display is mock_display

    def test_keyboard(self) -> None:
        mock_keyboard = MagicMock(spec_set=Keyboard)

        sut = Chip8(
            cores=[MagicMock(spec_set=Chip8Core)],
            bus=MagicMock(spec_set=DeviceBus),
            display=MagicMock(spec_set=Display),
            keyboard=mock_keyboard,
            instructions_per_update=16,
        )

        assert sut.keyboard is mock_keyboard
