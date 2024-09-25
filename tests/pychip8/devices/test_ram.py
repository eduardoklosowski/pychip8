from random import randint

from pychip8.devices.ram import Ram


class TestRam:
    def test_repr(self) -> None:
        for _ in range(10):
            size = randint(1, 4096)

            sut = Ram(size=size)

            assert repr(sut) == f'Ram(size={size})'

    def test_length(self) -> None:
        for _ in range(10):
            size = randint(1, 4096)

            sut = Ram(size=size)

            assert len(sut) == size

    def test_ran_should_start_with_zero(self) -> None:
        size = randint(64, 128)

        sut = Ram(size=size)

        for i in range(len(sut)):
            assert sut[i] == 0

    def test_read_write_addresses(self) -> None:
        for _ in range(10):
            sut = Ram(size=randint(1, 128))

            for i in range(len(sut)):
                assert sut[i] == 0
                sut[i] = i
                assert sut[i] == i
            for i in range(len(sut)):
                assert sut[i] == i

            for i in range(len(sut)):
                assert sut[i] == i
                sut[i] = 0
                assert sut[i] == 0
            for i in range(len(sut)):
                assert sut[i] == 0

    def test_write_overflow(self) -> None:
        sut = Ram(size=513)

        for i in range(255, 513):
            sut[i] = i
            assert sut[i] == i & 0xFF
