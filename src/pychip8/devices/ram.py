class Ram:
    def __init__(self, *, size: int) -> None:
        self._memory = [0 for _ in range(size)]

    def __repr__(self) -> str:
        return f'Ram(size={len(self)})'

    def __len__(self) -> int:
        return len(self._memory)

    def __getitem__(self, address: int, /) -> int:
        return self._memory[address]

    def __setitem__(self, address: int, value: int, /) -> None:
        self._memory[address] = value & 0xff
