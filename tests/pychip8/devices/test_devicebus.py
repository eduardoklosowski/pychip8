from io import BytesIO
from random import randint
from unittest.mock import MagicMock

import pytest

from pychip8.devices.devicebus import Device, DeviceBus


class TestDeviceBus:
    def test_repr(self) -> None:
        for _ in range(10):
            number_devices = randint(0, 10)

            sut = DeviceBus()
            for _ in range(number_devices):
                mock_device = MagicMock(spec_set=Device)
                sut.map(0, mock_device)

            assert repr(sut) == f'DeviceBus(devices={number_devices})'

    def test_length_with_empty_bus(self) -> None:
        sut = DeviceBus()

        assert len(sut) == 0

    def test_length_with_devices_in_order(self) -> None:
        for _ in range(10):
            sut = DeviceBus()

            address = 0
            for _ in range(10):
                size = randint(1, 1024)

                mock_device = MagicMock(spec_set=Device)
                mock_device.__len__.return_value = size

                sut.map(address, mock_device)

                address += size
                assert len(sut) == address

    def test_length_with_devices_in_diferent_order(self) -> None:
        for _ in range(10):
            mock_device1 = MagicMock(spec_set=Device)
            mock_device1.__len__.return_value = randint(1, 1024)

            mock_device2 = MagicMock(spec_set=Device)
            mock_device2.__len__.return_value = randint(1, 1024)

            sut = DeviceBus()
            sut.map(5000, mock_device1)
            sut.map(0, mock_device2)

            assert len(sut) == 5000 + len(mock_device1)

    def test_read_address_without_devices(self) -> None:
        sut = DeviceBus()

        with pytest.raises(RuntimeError, match=r'^Device not found for this address$'):
            sut[randint(0, 1024)]

    def test_read_address(self) -> None:
        for i in range(10):
            size1 = randint(1, 1024)
            start1 = randint(0 if i % 2 else 1024, 1024 - size1 if i % 2 else 2048 - size1)
            address1 = randint(start1, start1 + size1 - 1)
            value1 = object()

            size2 = randint(1, 1024)
            start2 = randint(1024 if i % 2 else 0, 2048 - size2 if i % 2 else 1024 - size2)
            address2 = randint(start2, start2 + size2 - 1)
            value2 = object()

            mock_device1 = MagicMock(spec_set=Device)
            mock_device1.__len__.return_value = size1
            mock_device1.__getitem__.return_value = value1

            mock_device2 = MagicMock(spec_set=Device)
            mock_device2.__len__.return_value = size2
            mock_device2.__getitem__.return_value = value2

            sut = DeviceBus()
            sut.map(start1, mock_device1)
            sut.map(start2, mock_device2)

            assert sut[address1] is value1
            mock_device1.__getitem__.assert_called_once_with(address1 - start1)
            assert sut[address2] is value2
            mock_device2.__getitem__.assert_called_once_with(address2 - start2)

    def test_read_address_not_found_device(self) -> None:
        for _ in range(10):
            size = randint(1, 1024)
            address = randint(100, 1024)

            mock_device = MagicMock(spec_set=Device)
            mock_device.__len__.return_value = size

            sut = DeviceBus()
            sut.map(address, mock_device)

            with pytest.raises(RuntimeError, match=r'^Device not found for this address$'):
                sut[randint(0, address - 1)]

            with pytest.raises(RuntimeError, match=r'^Device not found for this address$'):
                sut[randint(address + size, (address + size) * 2)]

    def test_write_address_without_devices(self) -> None:
        sut = DeviceBus()

        with pytest.raises(RuntimeError, match=r'^Device not found for this address$'):
            sut[randint(0, 1024)] = 0

    def test_write_address(self) -> None:
        for i in range(10):
            size1 = randint(1, 1024)
            start1 = randint(0 if i % 2 else 1024, 1024 - size1 if i % 2 else 2048 - size1)
            address1 = randint(start1, start1 + size1 - 1)
            value1 = randint(0, 255)

            size2 = randint(1, 1024)
            start2 = randint(1024 if i % 2 else 0, 2048 - size2 if i % 2 else 1024 - size2)
            address2 = randint(start2, start2 + size2 - 1)
            value2 = randint(0, 255)

            mock_device1 = MagicMock(spec_set=Device)
            mock_device1.__len__.return_value = size1

            mock_device2 = MagicMock(spec_set=Device)
            mock_device2.__len__.return_value = size2

            sut = DeviceBus()
            sut.map(start1, mock_device1)
            sut.map(start2, mock_device2)

            sut[address1] = value1
            sut[address2] = value2

            mock_device1.__setitem__.assert_called_once_with(address1 - start1, value1)
            mock_device2.__setitem__.assert_called_once_with(address2 - start2, value2)

    def test_write_address_not_found_device(self) -> None:
        for _ in range(10):
            size = randint(1, 1024)
            address = randint(100, 1024)

            mock_device = MagicMock(spec_set=Device)
            mock_device.__len__.return_value = size

            sut = DeviceBus()
            sut.map(address, mock_device)

            with pytest.raises(RuntimeError, match=r'^Device not found for this address$'):
                sut[randint(0, address - 1)] = 0

            with pytest.raises(RuntimeError, match=r'^Device not found for this address$'):
                sut[randint(address + size, (address + size) * 2)] = 0

    def test_load_program(self) -> None:
        for _ in range(10):
            address = randint(0, 2048)
            content = [randint(0, 255) for _ in range(randint(1, 512))]
            program = BytesIO(bytes(content))

            mock_device = MagicMock(spec_set=Device)
            mock_device.__len__.return_value = 4096

            sut = DeviceBus()
            sut.map(0, mock_device)

            sut.load_program(program, address)

            assert mock_device.__setitem__.call_count == len(content)
            for i, value in enumerate(content):
                mock_device.__setitem__.assert_any_call(address + i, value)

    def test_unmap_without_device_mapped(self) -> None:
        mock_device = MagicMock(spec_set=Device)

        sut = DeviceBus()

        sut.unmap_device(mock_device)

    def test_unmap_device(self) -> None:
        for _ in range(10):
            start = randint(0, 1024)
            size = randint(1, 1024)
            address = randint(start, start + size - 1)

            mock_device = MagicMock(spec_set=Device)
            mock_device.__len__.return_value = size

            sut = DeviceBus()
            sut.map(start, mock_device)

            sut[address]

            sut.unmap_device(mock_device)

            with pytest.raises(RuntimeError, match=r'^Device not found for this address$'):
                sut[address]

    def test_unmap_with_multiple_devices(self) -> None:
        for i in range(10):
            size1 = randint(1, 1024)
            start1 = randint(0 if i % 2 else 1024, 1024 - size1 if i % 2 else 2048 - size1)
            address1 = randint(start1, start1 + size1 - 1)

            size2 = randint(1, 1024)
            start2 = randint(1024 if i % 2 else 0, 2048 - size2 if i % 2 else 1024 - size2)
            address2 = randint(start2, start2 + size2 - 1)

            mock_device1 = MagicMock(spec_set=Device)
            mock_device1.__len__.return_value = size1

            mock_device2 = MagicMock(spec_set=Device)
            mock_device2.__len__.return_value = size2

            sut = DeviceBus()
            sut.map(start1, mock_device1)
            sut.map(start2, mock_device2)

            sut[address1]
            sut[address2]

            sut.unmap_device(mock_device2)

            sut[address1]
            with pytest.raises(RuntimeError, match=r'^Device not found for this address$'):
                sut[address2]

    def test_unmap_without_address_mapped(self) -> None:
        mock_device = MagicMock(spec_set=Device)

        sut = DeviceBus()

        sut.unmap_address(mock_device)

    def test_unmap_address(self) -> None:
        for _ in range(10):
            start = randint(0, 1024)
            size = randint(1, 1024)
            address = randint(start, start + size - 1)

            mock_device = MagicMock(spec_set=Device)
            mock_device.__len__.return_value = size

            sut = DeviceBus()
            sut.map(start, mock_device)

            sut[address]

            sut.unmap_address(start)

            with pytest.raises(RuntimeError, match=r'^Device not found for this address$'):
                sut[address]

    def test_unmap_with_multiple_addresses(self) -> None:
        for i in range(10):
            size1 = randint(1, 1024)
            start1 = randint(0 if i % 2 else 1024, 1024 - size1 if i % 2 else 2048 - size1)
            address1 = randint(start1, start1 + size1 - 1)

            size2 = randint(1, 1024)
            start2 = randint(1024 if i % 2 else 0, 2048 - size2 if i % 2 else 1024 - size2)
            address2 = randint(start2, start2 + size2 - 1)

            mock_device1 = MagicMock(spec_set=Device)
            mock_device1.__len__.return_value = size1

            mock_device2 = MagicMock(spec_set=Device)
            mock_device2.__len__.return_value = size2

            sut = DeviceBus()
            sut.map(start1, mock_device1)
            sut.map(start2, mock_device2)

            sut[address1]
            sut[address2]

            sut.unmap_address(start2)

            sut[address1]
            with pytest.raises(RuntimeError, match=r'^Device not found for this address$'):
                sut[address2]
