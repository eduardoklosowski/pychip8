from random import randint

import pytest

from pychip8.devices.rom import Rom


class TestRom:
    MINIMUM_SIZE = 16 * 5

    def test_repr(self) -> None:
        for _ in range(10):
            size = randint(self.MINIMUM_SIZE, self.MINIMUM_SIZE * 2)

            sut = Rom(size=size)

            assert repr(sut) == f'Rom(size={size})'

    def test_length_larger_than_minimum_size(self) -> None:
        for _ in range(10):
            size = randint(self.MINIMUM_SIZE, self.MINIMUM_SIZE * 2)

            sut = Rom(size=size)

            assert len(sut) == size

    def test_length_should_be_the_minimum_size(self) -> None:
        for _ in range(10):
            sut = Rom(size=randint(1, self.MINIMUM_SIZE - 1))

            assert len(sut) == self.MINIMUM_SIZE

    @pytest.mark.parametrize('i', range(16))
    def test_read_sprite(self, i: int) -> None:
        sut = Rom(size=randint(self.MINIMUM_SIZE, self.MINIMUM_SIZE * 2))

        for n in range(5):
            assert sut[i * 5 + n] == Rom.SPRITES[i][n]

    def test_read_zeros(self) -> None:
        size = randint(self.MINIMUM_SIZE, self.MINIMUM_SIZE * 2)

        sut = Rom(size=size)

        for i in range(self.MINIMUM_SIZE, size):
            assert sut[i] == 0

    def test_write_should_raise_error(self) -> None:
        sut = Rom(size=self.MINIMUM_SIZE)

        for _ in range(10):
            with pytest.raises(RuntimeError, match=r'^Writing on ROM$'):
                sut[randint(0, self.MINIMUM_SIZE)] = 0
