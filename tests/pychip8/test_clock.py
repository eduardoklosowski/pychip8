from itertools import count
from random import randint
from unittest.mock import MagicMock, patch

from pychip8.clock import clock


class TestClock:
    @patch('pychip8.clock.monotonic_ns')
    @patch('pychip8.clock.sleep')
    def test_run_without_sleep(self, mock_sleep: MagicMock, mock_monotonic: MagicMock) -> None:
        mock_monotonic.side_effect = count(start=1000, step=1000)
        mock_tickable = MagicMock()

        sut = clock(mock_tickable, 1_000_000)

        for i in range(1, randint(10, 50)):
            next(sut)

            assert mock_tickable.tick.call_count == i

        mock_sleep.assert_not_called()

    @patch('pychip8.clock.monotonic_ns')
    @patch('pychip8.clock.sleep')
    def test_run_with_sleep(self, mock_sleep: MagicMock, mock_monotonic: MagicMock) -> None:
        mock_monotonic.return_value = 0
        mock_tickable = MagicMock()

        sut = clock(mock_tickable, 1_000_000)

        for i in range(1, randint(10, 50)):
            next(sut)

            assert mock_tickable.tick.call_count == i
            assert mock_sleep.call_count == i
