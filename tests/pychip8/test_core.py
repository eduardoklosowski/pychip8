from collections.abc import Callable
from dataclasses import dataclass
from random import choice, randint
from unittest.mock import MagicMock, patch

import pytest

from pychip8.core import Chip8Core
from pychip8.devices.devicebus import DeviceBus
from pychip8.devices.display import Display
from pychip8.devices.keyboard import Future, Key, Keyboard


@dataclass
class MockBus:
    bus: DeviceBus
    memory: list[int]


@pytest.fixture
def mock_bus() -> MockBus:
    memory = [0 for _ in range(4096)]

    def read(x: int) -> int:
        return memory[x]

    def write(x: int, y: int) -> None:
        memory[x] = y

    mock_bus = MagicMock(spec_set=DeviceBus)
    mock_bus.__getitem__.side_effect = read
    mock_bus.__setitem__.side_effect = write

    return MockBus(mock_bus, memory)


class TestChip8Core:
    def test_repr(self) -> None:
        for _ in range(10):
            pc = randint(0, 4096)

            sut = Chip8Core(
                bus=MagicMock(spec_set=DeviceBus),
                reserved_address=0,
                display=MagicMock(spec_set=Display),
                keyboard=MagicMock(spec_set=Keyboard),
                entrypoint=pc,
                instructions_per_update=16,
            )

            assert repr(sut) == f'Chip8Core(pc={pc})'

    def test_tick(self) -> None:
        for _ in range(10):
            instructions_per_update = randint(1, 16)

            sut = Chip8Core(
                bus=MagicMock(spec_set=DeviceBus),
                reserved_address=0,
                display=MagicMock(spec_set=Display),
                keyboard=MagicMock(spec_set=Keyboard),
                entrypoint=0x200,
                instructions_per_update=instructions_per_update,
            )

            with (
                patch.object(sut, '_execute_instruction', spec_set=Callable) as mock_execute_instruction,
                patch.object(sut, '_decrement_timer', spec_set=Callable) as mock_decrement_time,
            ):
                for i in range(1, instructions_per_update * 3 + 1):
                    sut.tick()

                    assert mock_execute_instruction.call_count == i
                    assert mock_decrement_time.call_count == i // instructions_per_update

    def test_callbacks_in_tick(self) -> None:
        for _ in range(10):
            instructions_per_update = randint(1, 16)

            mock_tick_callback = MagicMock(spec_set=Callable)
            mock_update_callback = MagicMock(spec_set=Callable)

            sut = Chip8Core(
                bus=MagicMock(spec_set=DeviceBus),
                reserved_address=0,
                display=MagicMock(spec_set=Display),
                keyboard=MagicMock(spec_set=Keyboard),
                entrypoint=0x200,
                instructions_per_update=instructions_per_update,
            )
            sut.set_tick_callback(mock_tick_callback)
            sut.set_update_callback(mock_update_callback)

            with (
                patch.object(sut, '_execute_instruction', spec_set=Callable),
                patch.object(sut, '_decrement_timer', spec_set=Callable),
            ):
                for i in range(1, instructions_per_update * 3 + 1):
                    sut.tick()

                    assert mock_tick_callback.call_count == i
                    assert mock_update_callback.call_count == i // instructions_per_update

    def test_decrement_timers_with_zero(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=0,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        assert sut._delay_timer == 0
        assert sut._sound_timer == 0

        sut._decrement_timer()

        assert sut._delay_timer == 0
        assert sut._sound_timer == 0

    def test_decrement_delay_timer(self) -> None:
        timer = randint(5, 10)

        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=0,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )
        sut._delay_timer = timer

        for t in reversed(range(timer)):
            sut._decrement_timer()

            assert sut._delay_timer == t
            assert sut._sound_timer == 0

    def test_decrement_sound_timer(self) -> None:
        timer = randint(5, 10)

        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=0,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )
        sut._sound_timer = timer

        for t in reversed(range(timer)):
            sut._decrement_timer()

            assert sut._delay_timer == 0
            assert sut._sound_timer == t

    def test_decrement_all_timers(self) -> None:
        timer = randint(5, 10)

        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=0,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )
        sut._delay_timer = timer
        sut._sound_timer = timer

        for t in reversed(range(timer)):
            sut._decrement_timer()

            assert sut._delay_timer == t
            assert sut._sound_timer == t

    def test_instruction_sys(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            value = randint(0, 0xFFF)

            with pytest.raises(NotImplementedError, match=f'^Instruction {value:04x} not implemented$'):
                sut._instruction_sys(value)

    def test_execute_instruction_sys(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            while True:
                instruction = randint(0, 0x0FFF)
                if instruction not in (0x00E0, 0x00EE):
                    break

            sut._pc = address
            mock_bus.memory[address] = instruction >> 8
            mock_bus.memory[address + 1] = instruction & 0xFF

            with patch.object(sut, '_instruction_sys', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(instruction & 0xFFF)
                assert sut._pc == address + 2

    def test_instruction_jump(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFF)

            sut._instruction_jump(address)

            assert sut._pc == address

    def test_execute_instruction_jump(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 1
            nnn = randint(0, 0xFFF)

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | (nnn >> 8)
            mock_bus.memory[address + 1] = nnn & 0xFF

            with patch.object(sut, '_instruction_jump', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(nnn)
                assert sut._pc == address + 2

    def test_instruction_jump_v0(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xF00)
            v0 = randint(0, 0xFF)

            sut._v[0] = v0

            sut._instruction_jump_v0(address)

            assert sut._pc == address + v0

    def test_execute_instruction_jump_v0(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xB
            nnn = randint(0, 0xFFF)

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | (nnn >> 8)
            mock_bus.memory[address + 1] = nnn & 0xFF

            with patch.object(sut, '_instruction_jump_v0', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(nnn)
                assert sut._pc == address + 2

    def test_instruction_skip_eq_imediate(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xF00)

            for i in range(16):
                value = randint(0, 255)

                sut._pc = address
                sut._v[i] = value

                sut._instruction_skip_eq_imediate(i, value)

                assert sut._pc == address + 2

                sut._pc = address

                sut._instruction_skip_eq_imediate(i, (value + 1) & 0xFF)

                assert sut._pc == address

    def test_execute_instruction_skip_eq_imediate(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 3
            x = randint(0, 15)
            nn = randint(0, 0xFF)

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_skip_eq_imediate', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, nn)
                assert sut._pc == address + 2

    def test_instruction_skip_eq_register(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xF00)

            for i in range(16):
                j = choice([v for v in range(16) if v != i])
                value = randint(0, 255)

                sut._pc = address
                sut._v[i] = value
                sut._v[j] = value

                sut._instruction_skip_eq_register(i, j)

                assert sut._pc == address + 2

                sut._pc = address
                sut._v[j] = (value + 1) & 0xFF

                sut._instruction_skip_eq_register(i, j)

                assert sut._pc == address

    def test_execute_instruction_skip_eq_register(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 5
            x = randint(0, 15)
            y = randint(0, 15)
            n = 0

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = (y << 4) | n

            with patch.object(sut, '_instruction_skip_eq_register', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, y)
                assert sut._pc == address + 2

    def test_instruction_skip_ne_imediate(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xF00)

            for i in range(16):
                value = randint(0, 255)

                sut._pc = address
                sut._v[i] = value

                sut._instruction_skip_ne_imediate(i, (value + 1) & 0xFF)

                assert sut._pc == address + 2

                sut._pc = address

                sut._instruction_skip_ne_imediate(i, value)

                assert sut._pc == address

    def test_execute_instruction_skip_ne_imediate(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 4
            x = randint(0, 15)
            nn = randint(0, 0xFF)

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_skip_ne_imediate', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, nn)
                assert sut._pc == address + 2

    def test_instruction_skip_ne_register(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xF00)

            for i in range(16):
                j = choice([v for v in range(16) if v != i])
                value = randint(0, 255)

                sut._pc = address
                sut._v[i] = value
                sut._v[j] = (value + 1) & 0xFF

                sut._instruction_skip_ne_register(i, j)

                assert sut._pc == address + 2

                sut._pc = address
                sut._v[j] = value

                sut._instruction_skip_ne_register(i, j)

                assert sut._pc == address

    def test_execute_instruction_skip_ne_register(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 9
            x = randint(0, 15)
            y = randint(0, 15)
            n = 0

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = (y << 4) | n

            with patch.object(sut, '_instruction_skip_ne_register', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, y)
                assert sut._pc == address + 2

    def test_instruction_call_and_rts(self, mock_bus: MockBus) -> None:
        for _ in range(10):
            sut = Chip8Core(
                bus=mock_bus.bus,
                reserved_address=352,
                display=MagicMock(spec_set=Display),
                keyboard=MagicMock(spec_set=Keyboard),
                entrypoint=0x200,
                instructions_per_update=16,
            )
            addresses = [sut._pc]
            sp = sut._sp

            for _ in range(12):
                address = randint(0, 0xF00)
                addresses.append(address)
                sp += 2

                sut._instruction_call(address)

                assert sut._pc == address
                assert sut._sp == sp

            addresses.pop()
            for _ in range(12):
                address = addresses.pop()
                sp -= 2

                sut._instruction_rts()

                assert sut._pc == address
                assert sut._sp == sp

    def test_execute_instruction_call(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 2
            nnn = randint(0, 0xFFF)

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | (nnn >> 8)
            mock_bus.memory[address + 1] = nnn & 0xFF

            with patch.object(sut, '_instruction_call', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(nnn)
                assert sut._pc == address + 2

    def test_execute_instruction_rts(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            instruction = 0x00EE

            sut._pc = address
            mock_bus.memory[address] = instruction >> 8
            mock_bus.memory[address + 1] = instruction & 0xFF

            with patch.object(sut, '_instruction_rts', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with()
                assert sut._pc == address + 2

    def test_instruction_movm_to_i(self, mock_bus: MockBus) -> None:
        for x in range(16):
            values = [randint(0, 255) for _ in range(x + 1)]
            address = randint(0, 0xF00)

            sut = Chip8Core(
                bus=mock_bus.bus,
                reserved_address=352,
                display=MagicMock(spec_set=Display),
                keyboard=MagicMock(spec_set=Keyboard),
                entrypoint=0x200,
                instructions_per_update=16,
            )
            sut._i = address
            for x2, value in enumerate(values):
                sut._v[x2] = value

            sut._instruction_movm_to_i(x)

            assert sut._i == address + x + 1
            for x2, value in enumerate(values):
                assert mock_bus.memory[address + x2] == value

    def test_execute_instruction_movm_to_i(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xF
            x = randint(0, 15)
            nn = 0x55

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_movm_to_i', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x)
                assert sut._pc == address + 2

    def test_instruction_movm_from_i(self, mock_bus: MockBus) -> None:
        for x in range(16):
            values = [randint(0, 255) for _ in range(x + 1)]
            address = randint(0, 0xF00)
            for x2, value in enumerate(values):
                mock_bus.memory[address + x2] = value

            sut = Chip8Core(
                bus=mock_bus.bus,
                reserved_address=352,
                display=MagicMock(spec_set=Display),
                keyboard=MagicMock(spec_set=Keyboard),
                entrypoint=0x200,
                instructions_per_update=16,
            )
            sut._i = address

            sut._instruction_movm_from_i(x)

            assert sut._i == address + x + 1
            for x2, value in enumerate(values):
                assert sut._v[x2] == value

    def test_execute_instruction_movm_from_i(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xF
            x = randint(0, 15)
            nn = 0x65

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_movm_from_i', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x)
                assert sut._pc == address + 2

    def test_instruction_mov_imediate(self) -> None:
        for _ in range(10):
            values = [randint(0, 255) for _ in range(16)]

            sut = Chip8Core(
                bus=MagicMock(spec_set=DeviceBus),
                reserved_address=352,
                display=MagicMock(spec_set=Display),
                keyboard=MagicMock(spec_set=Keyboard),
                entrypoint=0x200,
                instructions_per_update=16,
            )

            for x, value in enumerate(values):
                sut._instruction_mov_imediate(x, value)

            for x, value in enumerate(values):
                assert sut._v[x] == value

    def test_execute_instruction_mov_imediate(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 6
            x = randint(0, 15)
            nn = randint(0, 0xFF)

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_mov_imediate', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, nn)
                assert sut._pc == address + 2

    def test_instruction_mov_register(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for x in range(16):
            values = [randint(0, 255) for _ in range(16)]
            for x2, value in enumerate(values):
                sut._v[x2] = value

            for y in range(16):
                sut._instruction_mov_register(x, y)

                assert sut._v[x] == sut._v[y]

    def test_execute_instruction_mov_register(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 8
            x = randint(0, 15)
            y = randint(0, 15)
            n = 0

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = (y << 4) | n

            with patch.object(sut, '_instruction_mov_register', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, y)
                assert sut._pc == address + 2

    def test_instruction_and(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for x in range(16):
            values = [randint(0, 255) for _ in range(16)]
            for x2, value in enumerate(values):
                sut._v[x2] = value

            for y in range(16):
                sut._v[x] = values[x]

                sut._instruction_and(x, y)

                assert sut._v[x] == values[x] & values[y]

    def test_execute_instruction_and(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 8
            x = randint(0, 15)
            y = randint(0, 15)
            n = 2

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = (y << 4) | n

            with patch.object(sut, '_instruction_and', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, y)
                assert sut._pc == address + 2

    def test_instruction_or(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for x in range(16):
            values = [randint(0, 255) for _ in range(16)]
            for x2, value in enumerate(values):
                sut._v[x2] = value

            for y in range(16):
                sut._v[x] = values[x]

                sut._instruction_or(x, y)

                assert sut._v[x] == values[x] | values[y]

    def test_execute_instruction_or(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 8
            x = randint(0, 15)
            y = randint(0, 15)
            n = 1

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = (y << 4) | n

            with patch.object(sut, '_instruction_or', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, y)
                assert sut._pc == address + 2

    def test_instruction_xor(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for x in range(16):
            values = [randint(0, 255) for _ in range(16)]
            for x2, value in enumerate(values):
                sut._v[x2] = value

            for y in range(16):
                sut._v[x] = values[x]

                sut._instruction_xor(x, y)

                assert sut._v[x] == values[x] ^ values[y]

    def test_execute_instruction_xor(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 8
            x = randint(0, 15)
            y = randint(0, 15)
            n = 3

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = (y << 4) | n

            with patch.object(sut, '_instruction_xor', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, y)
                assert sut._pc == address + 2

    def test_instruction_add_imediate(self) -> None:
        values = [randint(0, 255) for _ in range(16)]

        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for x, value in enumerate(values):
            sut._v[x] = value
            value2 = randint(0, 255)

            sut._instruction_add_imediate(x, value2)

            assert sut._v[x] == (value + value2) & 0xFF

    def test_execute_instruction_add_imediate(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 7
            x = randint(0, 15)
            nn = randint(0, 0xFF)

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_add_imediate', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, nn)
                assert sut._pc == address + 2

    def test_instruction_add_register(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for x in range(15):
            for y in range(15):
                value1 = randint(0, 255)
                value2 = randint(0, 255)
                total = value1 + value2 if x != y else value2 + value2

                sut._v[x] = value1
                sut._v[y] = value2

                sut._instruction_add_register(x, y)

                assert sut._v[x] == total & 0xFF
                assert sut._v[15] == total >> 8

    def test_execute_instruction_add_register(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 8
            x = randint(0, 15)
            y = randint(0, 15)
            n = 4

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = (y << 4) | n

            with patch.object(sut, '_instruction_add_register', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, y)
                assert sut._pc == address + 2

    def test_instruction_sub(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for x in range(15):
            for y in range(15):
                value1 = randint(0, 255)
                value2 = randint(0, 255)

                sut._v[x] = value1
                sut._v[y] = value2

                sut._instruction_sub(x, y)

                assert sut._v[x] == (value1 - value2 if x != y else 0) & 0xFF
                assert sut._v[15] == int(value1 > value2 if x != y else False)

    def test_execute_instruction_sub(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 8
            x = randint(0, 15)
            y = randint(0, 15)
            n = 5

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = (y << 4) | n

            with patch.object(sut, '_instruction_sub', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, y)
                assert sut._pc == address + 2

    def test_instruction_subb(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for x in range(15):
            for y in range(15):
                value1 = randint(0, 255)
                value2 = randint(0, 255)

                sut._v[x] = value1
                sut._v[y] = value2

                sut._instruction_subb(x, y)

                assert sut._v[x] == (value2 - value1 if x != y else 0) & 0xFF
                assert sut._v[15] == int(value2 > value1 if x != y else False)

    def test_execute_instruction_subb(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 8
            x = randint(0, 15)
            y = randint(0, 15)
            n = 7

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = (y << 4) | n

            with patch.object(sut, '_instruction_subb', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, y)
                assert sut._pc == address + 2

    def test_instruction_shr(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for x in range(15):
            for y in range(15):
                value = randint(0, 255)

                sut._v[y] = value

                sut._instruction_shr(x, y)

                assert sut._v[x] == value >> 1
                assert sut._v[15] == value & 1

    def test_execute_instruction_shr(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 8
            x = randint(0, 15)
            y = randint(0, 15)
            n = 6

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = (y << 4) | n

            with patch.object(sut, '_instruction_shr', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, y)
                assert sut._pc == address + 2

    def test_instruction_shl(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for x in range(15):
            for y in range(15):
                value = randint(0, 255)

                sut._v[y] = value

                sut._instruction_shl(x, y)

                assert sut._v[x] == (value << 1) & 0xFF
                assert sut._v[15] == value >> 7

    def test_execute_instruction_shl(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 8
            x = randint(0, 15)
            y = randint(0, 15)
            n = 0xE

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = (y << 4) | n

            with patch.object(sut, '_instruction_shl', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, y)
                assert sut._pc == address + 2

    def test_instruction_cls(self) -> None:
        mock_display = MagicMock(spec_set=Display)

        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=mock_display,
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        sut._instruction_cls()

        mock_display.clear.assert_called_once_with()

    def test_execute_instruction_cls(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            instruction = 0x00E0

            sut._pc = address
            mock_bus.memory[address] = instruction >> 8
            mock_bus.memory[address + 1] = instruction & 0xFF

            with patch.object(sut, '_instruction_cls', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with()
                assert sut._pc == address + 2

    def test_instruction_sprite(self, mock_bus: MockBus) -> None:
        for _ in range(10):
            x = randint(0, 64)
            y = randint(0, 32)
            vx = randint(0, 14)
            vy = choice([i for i in range(15) if i != vx])
            n = randint(1, 10)
            values = [randint(0, 255) for _ in range(n)]
            address = randint(0, 0xF00)
            for i, value in enumerate(values):
                mock_bus.memory[address + i] = value
            flipped = choice([True, False])

            mock_display = MagicMock(spec_set=Display)
            mock_display.draw_sprite.return_value = flipped

            sut = Chip8Core(
                bus=mock_bus.bus,
                reserved_address=352,
                display=mock_display,
                keyboard=MagicMock(spec_set=Keyboard),
                entrypoint=0x200,
                instructions_per_update=16,
            )
            sut._i = address
            sut._v[vx] = x
            sut._v[vy] = y

            sut._instruction_sprite(vx, vy, n)

            mock_display.draw_sprite.assert_called_once_with(x, y, values)
            assert sut._v[15] == int(flipped)

    def test_execute_instruction_sprite(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xD
            x = randint(0, 15)
            y = randint(0, 15)
            n = randint(0, 0xF)

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = (y << 4) | n

            with patch.object(sut, '_instruction_sprite', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, y, n)
                assert sut._pc == address + 2

    @pytest.mark.parametrize('i', range(16))
    def test_instruction_spritechar(self, i: int) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            x = randint(0, 15)

            sut._v[x] = i

            sut._instruction_spritechar(x)

            assert sut._i == i * 5

    def test_execute_instruction_spritechar(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xF
            x = randint(0, 15)
            nn = 0x29

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_spritechar', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x)
                assert sut._pc == address + 2

    def test_instruction_mov_to_i(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFF)

            sut._instruction_mov_to_i(address)

            assert sut._i == address

    def test_execute_instruction_mov_to_i(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xA
            nnn = randint(0, 0xFFF)

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | (nnn >> 8)
            mock_bus.memory[address + 1] = nnn & 0xFF

            with patch.object(sut, '_instruction_mov_to_i', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(nnn)
                assert sut._pc == address + 2

    def test_instruction_add_to_i(self) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            i = randint(0, 0xFFF)
            x = randint(0, 15)
            value = randint(0, 255)

            sut._i = i
            sut._v[x] = value

            sut._instruction_add_to_i(x)

            assert sut._i == (i + value) & 0xFFF

    def test_execute_instruction_add_to_i(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xF
            x = randint(0, 15)
            nn = 0x1E

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_add_to_i', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x)
                assert sut._pc == address + 2

    @pytest.mark.parametrize('key', Key)
    def test_instruction_skip_key(self, key: Key) -> None:
        for _ in range(10):
            address = randint(0, 0xF00)
            x = randint(0, 15)

            mock_keyboard = MagicMock(spec_set=Keyboard)

            sut = Chip8Core(
                bus=MagicMock(spec_set=DeviceBus),
                reserved_address=352,
                display=MagicMock(spec_set=Display),
                keyboard=mock_keyboard,
                entrypoint=0x200,
                instructions_per_update=16,
            )
            sut._v[x] = int(key)

            mock_keyboard.__getitem__.return_value = False
            sut._pc = address

            sut._instruction_skip_key(x)

            assert sut._pc == address

            mock_keyboard.__getitem__.return_value = True
            sut._pc = address

            sut._instruction_skip_key(x)

            assert sut._pc == address + 2

    def test_execute_instruction_skip_key(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xE
            x = randint(0, 15)
            nn = 0x9E

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_skip_key', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x)
                assert sut._pc == address + 2

    @pytest.mark.parametrize('key', Key)
    def test_instruction_skip_nokey(self, key: Key) -> None:
        for _ in range(10):
            address = randint(0, 0xF00)
            x = randint(0, 15)

            mock_keyboard = MagicMock(spec_set=Keyboard)

            sut = Chip8Core(
                bus=MagicMock(spec_set=DeviceBus),
                reserved_address=352,
                display=MagicMock(spec_set=Display),
                keyboard=mock_keyboard,
                entrypoint=0x200,
                instructions_per_update=16,
            )
            sut._v[x] = int(key)

            mock_keyboard.__getitem__.return_value = True
            sut._pc = address

            sut._instruction_skip_nokey(x)

            assert sut._pc == address

            mock_keyboard.__getitem__.return_value = False
            sut._pc = address

            sut._instruction_skip_nokey(x)

            assert sut._pc == address + 2

    def test_execute_instruction_skip_nokey(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xE
            x = randint(0, 15)
            nn = 0xA1

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_skip_nokey', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x)
                assert sut._pc == address + 2

    @pytest.mark.parametrize('key', Key)
    def test_instruction_wait_key(self, key: Key) -> None:
        for _ in range(10):
            address = randint(2, 0xFFF)
            x = randint(0, 15)
            future: Future[Key] = Future()

            mock_keyboard = MagicMock(spec_set=Keyboard)
            mock_keyboard.next_key_pressed.return_value = future

            sut = Chip8Core(
                bus=MagicMock(spec_set=DeviceBus),
                reserved_address=352,
                display=MagicMock(spec_set=Display),
                keyboard=mock_keyboard,
                entrypoint=0x200,
                instructions_per_update=16,
            )

            for _ in range(randint(1, 10)):
                sut._pc = address

                sut._instruction_wait_key(x)

                assert sut._pc == address - 2

            future.set_result(key)
            sut._pc = address

            sut._instruction_wait_key(x)

            assert sut._v[x] == key
            assert sut._pc == address

    def test_execute_instruction_wait_key(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xF
            x = randint(0, 15)
            nn = 0x0A

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_wait_key', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x)
                assert sut._pc == address + 2

    @pytest.mark.parametrize('x', range(16))
    def test_instruction_mov_from_delay(self, x: int) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            value = randint(0, 255)

            sut._delay_timer = value

            sut._instruction_mov_from_delay(x)

            assert sut._v[x] == value

    def test_execute_instruction_mov_from_delay(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xF
            x = randint(0, 15)
            nn = 0x07

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_mov_from_delay', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x)
                assert sut._pc == address + 2

    @pytest.mark.parametrize('x', range(16))
    def test_instruction_mov_to_delay(self, x: int) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            value = randint(0, 255)

            sut._v[x] = value

            sut._instruction_mov_to_delay(x)

            assert sut._delay_timer == value

    def test_execute_instruction_mov_to_delay(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xF
            x = randint(0, 15)
            nn = 0x15

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_mov_to_delay', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x)
                assert sut._pc == address + 2

    @pytest.mark.parametrize('x', range(16))
    def test_instruction_mov_to_sound(self, x: int) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            value = randint(0, 255)

            sut._v[x] = value

            sut._instruction_mov_to_sound(x)

            assert sut._sound_timer == value

    def test_execute_instruction_mov_to_sound(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xF
            x = randint(0, 15)
            nn = 0x18

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_mov_to_sound', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x)
                assert sut._pc == address + 2

    @pytest.mark.parametrize('x', range(16))
    def test_instruction_rnd(self, x: int) -> None:
        sut = Chip8Core(
            bus=MagicMock(spec_set=DeviceBus),
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            value = randint(0, 255)
            nn = randint(0, 255)

            with patch('pychip8.core.randbits', spec_set=Callable) as mock_randbits:
                mock_randbits.return_value = value

                sut._instruction_rnd(x, nn)

                mock_randbits.assert_called_once_with(8)
                assert sut._v[x] == value & nn

    def test_execute_instruction_rnd(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xC
            x = randint(0, 15)
            nn = randint(0, 0xFF)

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_rnd', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x, nn)
                assert sut._pc == address + 2

    @pytest.mark.parametrize('x', range(16))
    def test_instruction_movbcd(self, mock_bus: MockBus, x: int) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xF00)
            value = randint(0, 255)

            sut._i = address
            sut._v[x] = value

            sut._instruction_movbcd(x)

            assert mock_bus.memory[address] == value // 100
            assert mock_bus.memory[address + 1] == value // 10 % 10
            assert mock_bus.memory[address + 2] == value % 10

    def test_execute_instruction_movbcd(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xF
            x = randint(0, 15)
            nn = 0x33

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with patch.object(sut, '_instruction_movbcd', spec_set=Callable) as mock_instruction:
                sut._execute_instruction()

                mock_instruction.assert_called_once_with(x)
                assert sut._pc == address + 2

    def test_execute_undefined_instruction(self, mock_bus: MockBus) -> None:
        sut = Chip8Core(
            bus=mock_bus.bus,
            reserved_address=352,
            display=MagicMock(spec_set=Display),
            keyboard=MagicMock(spec_set=Keyboard),
            entrypoint=0x200,
            instructions_per_update=16,
        )

        for _ in range(10):
            address = randint(0, 0xFFE)
            op = 0xF
            x = randint(0, 15)
            nn = randint(0x66, 0xFF)

            sut._pc = address
            mock_bus.memory[address] = (op << 4) | x
            mock_bus.memory[address + 1] = nn

            with pytest.raises(RuntimeError, match=r'^Undefined instruction$'):
                sut._execute_instruction()
