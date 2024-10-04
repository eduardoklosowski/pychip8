from collections.abc import Callable
from math import ceil
from random import choice, randint
from unittest.mock import MagicMock

from pychip8.devices.display import AddressableDisplay, Display


class TestDisplay:
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

            assert str(sut) == '\n'.join(Display.PIXEL_OFF * width for _ in range(height))

    def test_str_full_display(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)

            sut = Display(width=width, height=height)
            for y in range(height):
                for x in range(width):
                    sut.set_pixel(x, y, True)

            assert str(sut) == '\n'.join(Display.PIXEL_ON * width for _ in range(height))

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
                ''.join(Display.PIXEL_ON if pixel else Display.PIXEL_OFF for pixel in line) for line in frame
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

        mock_callback = MagicMock(spec_set=Callable)

        sut = Display(width=width, height=height)
        sut.set_clear_callback(mock_callback)

        mock_callback.assert_not_called()

        sut.clear()

        mock_callback.assert_called_once_with()

    def test_refresh(self) -> None:
        for _ in range(10):
            width = randint(1, 16)
            height = randint(1, 8)
            frame = [[choice([True, False]) for _ in range(width)] for _ in range(height)]

            mock_callback = MagicMock(spec_set=Callable)
            sut = Display(width=width, height=height)
            for y in range(height):
                for x in range(width):
                    sut.set_pixel(x, y, frame[y][x])
            sut.set_update_pixel_callback(mock_callback)

            sut.refresh()

            assert mock_callback.call_count == sut.width * sut.height
            for y in range(height):
                for x in range(width):
                    mock_callback.assert_any_call(x, y, frame[y][x])

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

            mock_callback = MagicMock(spec_set=Callable)

            sut = Display(width=width, height=height)
            sut.set_update_pixel_callback(mock_callback)

            mock_callback.assert_not_called()

            sut.set_pixel(x, y, value)

            mock_callback.assert_called_once_with(x, y, value)

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
            sprite = [0xF0, 0xF0, 0xF0, 0xF0]
            pixels1 = {(x % width, y % height) for x in range(x1, x1 + 4) for y in range(y1, y1 + 4)}
            pixels2 = {(x % width, y % height) for x in range(x2, x2 + 4) for y in range(y2, y2 + 4)}
            pixels = pixels1.difference(pixels2) | pixels2.difference(pixels1)

            sut = Display(width=width, height=height)
            assert sut.draw_sprite(x1, y1, sprite) is False
            assert sut.draw_sprite(x2, y2, sprite) is True

            for y in range(height):
                for x in range(width):
                    assert sut.get_pixel(x, y) is ((x, y) in pixels)


class TestAddressableDisplay:
    def test_repr(self) -> None:
        for _ in range(10):
            mock_display = MagicMock(spec_set=Display)

            sut = AddressableDisplay(mock_display)

            assert repr(sut) == f'AddressableDisplay({mock_display!r})'

    def test_length(self) -> None:
        for _ in range(10):
            width = randint(1, 32)
            height = randint(1, 16)

            for i in range(9):
                mock_display = MagicMock(spec_set=Display)
                mock_display.width = width + i
                mock_display.height = height
                sut = AddressableDisplay(mock_display)
                assert len(sut) == ceil((width + i) * height / 8)

                mock_display = MagicMock(spec_set=Display)
                mock_display.width = width
                mock_display.height = height + i
                sut = AddressableDisplay(mock_display)
                assert len(sut) == ceil(width * (height + i) / 8)

    def test_read_address(self) -> None:
        for _ in range(10):
            width = randint(2, 32)
            height = randint(4, 16)
            value = randint(0, 255)
            address = randint(0, ceil(width * height / 8))

            display = Display(width=width, height=height)
            for i, pixel_number in enumerate(range(address * 8, (address + 1) * 8)):
                pixel = bool(value >> (7 - i) & 1)
                x = pixel_number % width
                y = pixel_number // width
                display.set_pixel(x, y, pixel)
            sut = AddressableDisplay(display)

            assert sut[address] == value

    def test_write_address(self) -> None:
        for _ in range(10):
            width = randint(2, 32)
            height = randint(4, 16)
            value = randint(0, 255)
            address = randint(0, ceil(width * height / 8))
            pixels = {
                (pixel_number % width, pixel_number // width % height)
                for i, pixel_number in enumerate(range(address * 8, (address + 1) * 8))
                if bool(value >> (7 - i) & 1)
            }

            display = Display(width=width, height=height)
            sut = AddressableDisplay(display)

            sut[address] = value

            for y in range(height):
                for x in range(width):
                    assert display.get_pixel(x, y) is ((x, y) in pixels)
