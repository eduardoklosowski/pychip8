from random import choice, randint
from unittest.mock import MagicMock

from pychip8.devices.display import Display


class TestDisplay:
    BLACK = ' '
    WHITE = '\u2588'

    def test_repr(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)

            sut = Display(width=width, height=height)

            assert repr(sut) == f'Display({width}x{height})'

    def test_str_clean_display(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)

            sut = Display(width=width, height=height)

            assert str(sut) == '\n'.join(self.BLACK * width for _ in range(height))

    def test_str_full_display(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)

            sut = Display(width=width, height=height)
            for y in range(height):
                for x in range(width):
                    sut.set_pixel(x, y, True)

            assert str(sut) == '\n'.join(self.WHITE * width for _ in range(height))

    def test_str_random_values(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)
            frame = [[choice([True, False]) for _ in range(width)] for _ in range(height)]

            sut = Display(width=width, height=height)
            for y in range(height):
                for x in range(width):
                    sut.set_pixel(x, y, frame[y][x])

            assert str(sut) == '\n'.join(
                ''.join(
                    self.WHITE if pixel else self.BLACK
                    for pixel in line
                )
                for line in frame
            )

    def test_size(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)

            sut = Display(width=width, height=height)

            assert sut.width == width
            assert sut.height == height

    def test_start_with_clear_display(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)

            sut = Display(width=width, height=height)

            for y in range(height):
                for x in range(width):
                    assert sut.get_pixel(x, y) is False

    def test_clear_display(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)

            sut = Display(width=width, height=height)
            for y in range(height):
                for x in range(width):
                    sut.set_pixel(x, y, True)

            sut.clear()

            for y in range(height):
                for x in range(width):
                    assert sut.get_pixel(x, y) is False

    def test_clear_should_call_clear_callback(self) -> None:
        width = randint(1, 32)
        height = randint(1, 16)

        callback = MagicMock()

        sut = Display(width=width, height=height)
        sut.set_clear_callback(callback)

        callback.assert_not_called()

        sut.clear()

        callback.assert_called_once_with()

    def test_refresh(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)
            frame = [[choice([True, False]) for _ in range(width)] for _ in range(height)]

            callback = MagicMock()
            sut = Display(width=width, height=height)
            for y in range(height):
                for x in range(width):
                    sut.set_pixel(x, y, frame[y][x])
            sut.set_update_pixel_callback(callback)

            sut.refresh()

            assert callback.call_count == sut.width * sut.height
            for y in range(height):
                for x in range(width):
                    callback.assert_any_call(x, y, frame[y][x])

    def test_refresh_witchout_callback(self) -> None:
        sut = Display(width=randint(1, 32), height=randint(1, 16))

        sut.refresh()

    def test_read_write_pixel(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)

            sut = Display(width=width, height=height)

            for y in range(height):
                for x in range(width):
                    assert sut.get_pixel(x, y) is False
                    sut.set_pixel(x, y, True)
                    assert sut.get_pixel(x, y) is True
            for y in range(height):
                for x in range(width):
                    assert sut.get_pixel(x, y) is True

            for y in range(height):
                for x in range(width):
                    assert sut.get_pixel(x, y) is True
                    sut.set_pixel(x, y, False)
                    assert sut.get_pixel(x, y) is False
            for y in range(height):
                for x in range(width):
                    assert sut.get_pixel(x, y) is False

    def test_read_off_screen_pixel(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)

            sut = Display(width=width, height=height)

            for y in range(height):
                for x in range(width):
                    assert sut.get_pixel(x + width, y) is False
                    assert sut.get_pixel(x, y + height) is False
                    assert sut.get_pixel(x + width, y + height) is False
                    sut.set_pixel(x, y, True)
                    assert sut.get_pixel(x + width, y) is True
                    assert sut.get_pixel(x, y + height) is True
                    assert sut.get_pixel(x + width, y + height) is True

    def test_write_off_screen_pixel(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)

            sut = Display(width=width, height=height)

            for y in range(height):
                for x in range(width):
                    sut.set_pixel(x + width, y, True)
                    assert sut.get_pixel(x, y) is True
                    sut.set_pixel(x, y, False)

                    sut.set_pixel(x, y + height, True)
                    assert sut.get_pixel(x, y) is True
                    sut.set_pixel(x, y, False)

                    sut.set_pixel(x + width, y + height, True)
                    assert sut.get_pixel(x, y) is True

    def test_flipped_pixel(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)
            x = randint(0, width - 1)
            y = randint(0, height - 1)

            sut = Display(width=width, height=height)

            assert sut.set_pixel(x, y, True) is False
            assert sut.get_pixel(x, y) is True
            assert sut.set_pixel(x, y, True) is True
            assert sut.get_pixel(x, y) is False

    def test_false_do_not_flip_pixel(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)
            x = randint(0, width - 1)
            y = randint(0, height - 1)

            sut = Display(width=width, height=height)

            assert sut.set_pixel(x, y, True) is False
            assert sut.get_pixel(x, y) is True
            assert sut.set_pixel(x, y, False) is False
            assert sut.get_pixel(x, y) is False
            assert sut.set_pixel(x, y, False) is False
            assert sut.get_pixel(x, y) is False

    def test_set_pixel_should_call_update_pixel_callback(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)
            x = randint(0, width - 1)
            y = randint(0, height - 1)
            value = choice([True, False])

            callback = MagicMock()

            sut = Display(width=width, height=height)
            sut.set_update_pixel_callback(callback)

            callback.assert_not_called()

            sut.set_pixel(x, y, value)

            callback.assert_called_once_with(x, y, value)

    def test_draw_sprite(self) -> None:
        for _ in range(10):
            width = randint(32, 64)
            height = randint(16, 32)
            x = randint(0, width - 1)
            y = randint(0, height - 1)
            sprite = [randint(1, 255) for _ in range(randint(1, 10))]
            pixels = {
                ((x + x2) % width, (y + y2) % height)
                for y2, line in enumerate(sprite)
                for x2, pixel in enumerate(f'{line:08b}')
                if pixel == '1'
            }

            sut = Display(width=width, height=height)

            assert sut.draw_sprite(x, y, sprite) is False

            for y in range(height):
                for x in range(width):
                    assert sut.get_pixel(x, y) is ((x, y) in pixels)

    def test_draw_sprite_with_collision(self) -> None:
        for _ in range(10):
            width = randint(32, 64)
            height = randint(16, 32)
            x1 = randint(0, width - 1)
            y1 = randint(0, height - 1)
            x2 = randint(x1 - 3, x1 + 3)
            y2 = randint(y1 - 3, y1 + 3)
            sprite = [0xf0, 0xf0, 0xf0, 0xf0]
            pixels1 = {(x % width, y % height) for x in range(x1, x1 + 4) for y in range(y1, y1 + 4)}
            pixels2 = {(x % width, y % height) for x in range(x2, x2 + 4) for y in range(y2, y2 + 4)}
            pixels = pixels1.difference(pixels2) | pixels2.difference(pixels1)

            sut = Display(width=width, height=height)
            assert sut.draw_sprite(x1, y1, sprite) is False
            assert sut.draw_sprite(x2, y2, sprite) is True

            for y in range(height):
                for x in range(width):
                    assert sut.get_pixel(x, y) is ((x, y) in pixels)
