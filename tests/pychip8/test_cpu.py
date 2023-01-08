from io import BytesIO
from random import randint
from unittest.mock import MagicMock

from pychip8.cpu import Chip8


class TestChip8:
    def test_repr(self) -> None:
        for i in range(10):
            sut = Chip8(
                cores=[MagicMock() for _ in range(i)],
                bus=MagicMock(),
                display=MagicMock(),
                keyboard=MagicMock(),
                instructions_per_update=16,
            )

            assert repr(sut) == f'Chip8(cores={i})'

    def test_length(self) -> None:
        for i in range(10):
            sut = Chip8(
                cores=[MagicMock() for _ in range(i)],
                bus=MagicMock(),
                display=MagicMock(),
                keyboard=MagicMock(),
                instructions_per_update=16,
            )

            assert len(sut) == i

    def test_load_program(self) -> None:
        for _ in range(10):
            content = [randint(0, 255) for _ in range(randint(1, 512))]
            program = BytesIO(bytes(content))

            bus = MagicMock()

            sut = Chip8(
                cores=[MagicMock()],
                bus=bus,
                display=MagicMock(),
                keyboard=MagicMock(),
                instructions_per_update=16,
            )

            sut.load_program(program)

            bus.load_program.assert_called_once_with(program, 0x200)

    def test_load_program_with_load_at(self) -> None:
        for _ in range(10):
            address = randint(0, 2048)
            content = [randint(0, 255) for _ in range(randint(1, 512))]
            program = BytesIO(bytes(content))

            bus = MagicMock()

            sut = Chip8(
                cores=[MagicMock()],
                bus=bus,
                display=MagicMock(),
                keyboard=MagicMock(),
                instructions_per_update=16,
            )

            sut.load_program(program, load_at=address)

            bus.load_program.assert_called_once_with(program, address)

    def test_tick(self) -> None:
        for i in range(10):
            instructions_per_update = randint(1, 16)
            cores = [MagicMock() for _ in range(i)]

            sut = Chip8(
                cores=cores,  # type: ignore
                bus=MagicMock(),
                display=MagicMock(),
                keyboard=MagicMock(),
                instructions_per_update=16,
            )

            for j in range(1, instructions_per_update * 3 + 1):
                sut.tick()

                for core in cores:
                    assert core.tick.call_count == j

    def test_callbacks_in_tick(self) -> None:
        for i in range(10):
            instructions_per_update = randint(1, 16)
            cores = [MagicMock() for _ in range(i)]

            tick_callback = MagicMock()
            update_callback = MagicMock()

            sut = Chip8(
                cores=cores,  # type: ignore
                bus=MagicMock(),
                display=MagicMock(),
                keyboard=MagicMock(),
                instructions_per_update=instructions_per_update,
            )
            sut.set_tick_callback(tick_callback)
            sut.set_update_callback(update_callback)

            for j in range(1, instructions_per_update * 3 + 1):
                sut.tick()

                assert tick_callback.call_count == j
                assert update_callback.call_count == j // instructions_per_update
