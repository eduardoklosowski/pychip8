from typing import BinaryIO, Protocol


class Device(Protocol):
    def __len__(self) -> int: ...

    def __getitem__(self, address: int, /) -> int: ...

    def __setitem__(self, address: int, value: int, /) -> None: ...


class DeviceBus:
    def __init__(self) -> None:
        self._devices: list[tuple[int, int, Device]] = []

    def __repr__(self) -> str:
        return f'DeviceBus(devices={len(self._devices)})'

    def __len__(self) -> int:
        return max((end + 1 for _, end, _ in self._devices), default=0)

    def __getitem__(self, address: int, /) -> int:
        for start, end, device in self._devices:
            if start <= address <= end:
                return device[address - start]
        raise RuntimeError('Device not found for this address')

    def __setitem__(self, address: int, value: int, /) -> None:
        for start, end, device in self._devices:
            if start <= address <= end:
                device[address - start] = value
                return
        raise RuntimeError('Device not found for this address')

    def load_program(self, program: BinaryIO, load_at: int, /) -> None:
        for i, b in enumerate(program.read()):
            self[load_at + i] = b

    def map(self, start: int, device: Device, /) -> None:
        self._devices.append((start, start + len(device) - 1, device))

    def unmap_device(self, device: Device, /) -> None:
        for i, (_, _, device2) in enumerate(self._devices):
            if device == device2:
                self._devices.pop(i)
                return

    def unmap_address(self, address: int, /) -> None:
        for i, (start, _, _) in enumerate(self._devices):
            if address == start:
                self._devices.pop(i)
                return
