from random import choices

import pytest

from pychip8.devices.keyboard import Key, Keyboard


class TestKey:
    def test_count_keys(self) -> None:
        assert len(Key) == 16

    def test_keys(self) -> None:
        for k in range(len(Key)):
            assert Key(k).value == k


class TestKeyboard:
    def test_repr_without_key_pressed(self) -> None:
        sut = Keyboard()

        assert repr(sut) == 'Keyboard(pressed="")'

    @pytest.mark.parametrize('key', Key)
    def test_repr_with_key_pressed(self, key: Key) -> None:
        sut = Keyboard()
        sut[key] = True

        assert repr(sut) == f'Keyboard(pressed="{key:X}")'

    def test_repr_with_all_keys_pressed(self) -> None:
        sut = Keyboard()
        for key in Key:
            sut[key] = True

        assert repr(sut) == f'Keyboard(pressed="{", ".join(f"{i:X}" for i in range(len(Key)))}")'

    def test_keyboard_size(self) -> None:
        sut = Keyboard()

        assert len(sut) == len(Key)

    def test_keyboard_start_without_key_pressed(self) -> None:
        sut = Keyboard()

        for k in Key:
            assert sut[k] is False

    @pytest.mark.parametrize('key', Key)
    def test_press_one_key(self, key: Key) -> None:
        sut = Keyboard()

        sut[key] = True
        for k in Key:
            assert sut[k] is (k == key)

        sut[key] = False
        for k in Key:
            assert sut[k] is False

    @pytest.mark.parametrize('key', Key)
    def test_double_press_same_key(self, key: Key) -> None:
        sut = Keyboard()

        sut[key] = True
        sut[key] = True
        for k in Key:
            assert sut[k] is (k == key)

        sut[key] = False
        for k in Key:
            assert sut[k] is False

        sut[key] = False
        for k in Key:
            assert sut[k] is False

    def test_press_all_keys(self) -> None:
        sut = Keyboard()

        for key in Key:
            assert sut[key] is False
            sut[key] = True
            assert sut[key] is True
        for key in Key:
            assert sut[key] is True

        for key in Key:
            assert sut[key] is True
            sut[key] = False
            assert sut[key] is False
        for key in Key:
            assert sut[key] is False

    @pytest.mark.parametrize('key', Key)
    def test_next_key_pressed(self, key: Key) -> None:
        sut = Keyboard()
        key_pressed = sut.next_key_pressed()

        assert key_pressed.done() is False

        sut[key] = True
        assert key_pressed.done() is True
        assert key_pressed.result() == key

    @pytest.mark.parametrize('key', Key)
    def test_next_key_pressed_not_result_key_up(self, key: Key) -> None:
        sut = Keyboard()
        key_pressed = sut.next_key_pressed()

        sut[key] = False
        assert key_pressed.done() is False

        sut[key] = True
        assert key_pressed.done() is True
        assert key_pressed.result() == key

    def test_next_key_pressed_should_return_first_key_pressed(self) -> None:
        for _ in range(10):
            key1, key2 = choices(list(Key), k=2)

            sut = Keyboard()
            key_pressed = sut.next_key_pressed()

            sut[key1] = True
            sut[key2] = True
            assert key_pressed.done() is True
            assert key_pressed.result() == key1

    def test_next_key_pressed_should_resolve_all_futures_with_fist_key_pressed(self) -> None:
        for _ in range(10):
            key1, key2 = choices(list(Key), k=2)

            sut = Keyboard()
            key_pressed1 = sut.next_key_pressed()
            key_pressed2 = sut.next_key_pressed()

            sut[key1] = True
            assert key_pressed1.done() is True
            assert key_pressed1.result() == key1
            assert key_pressed2.done() is True
            assert key_pressed2.result() == key1

            key_pressed3 = sut.next_key_pressed()

            sut[key2] = True
            assert key_pressed3.done() is True
            assert key_pressed3.result() == key2

    @pytest.mark.parametrize('key', Key)
    @pytest.mark.parametrize('i', [0, 1])
    def test_cancel_one_next_key_pressed_should_not_cancel_the_other(self, key: Key, i: int) -> None:
        j = (i + 1) % 2
        sut = Keyboard()
        key_pressed = [sut.next_key_pressed(), sut.next_key_pressed()]

        key_pressed[i].cancel()
        sut[key] = True

        assert key_pressed[i].cancelled() is True

        assert key_pressed[j].cancelled() is False
        assert key_pressed[j].done() is True
        assert key_pressed[j].result() == key
