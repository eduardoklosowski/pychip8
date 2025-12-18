from collections.abc import Callable
from secrets import randbits

from .devices.devicebus import DeviceBus
from .devices.display import Display
from .devices.keyboard import Future, Key, Keyboard


class Chip8Core:
    def __init__(
        self,
        *,
        bus: DeviceBus,
        reserved_address: int,
        display: Display,
        keyboard: Keyboard,
        entrypoint: int,
        instructions_per_update: int,
    ) -> None:
        self._bus = bus
        self._display = display
        self._keyboard = keyboard
        self._v = [0 for _ in range(16)]
        self._i = 0
        self._sp = len(bus) - reserved_address - 2
        self._pc = entrypoint
        self._delay_timer = 0
        self._sound_timer = 0
        self._waiting_keyboard: Future[Key] | None = None
        self._instructions_per_update = instructions_per_update
        self._instructions_executable = 0
        self._tick_callback: Callable[[], None] | None = None
        self._update_callback: Callable[[], None] | None = None

    def __repr__(self) -> str:
        return f'Chip8Core(pc={self._pc})'

    def set_tick_callback(self, callback: Callable[[], None] | None, /) -> None:
        self._tick_callback = callback

    def set_update_callback(self, callback: Callable[[], None] | None, /) -> None:
        self._update_callback = callback

    def tick(self) -> None:
        self._execute_instruction()
        if self._tick_callback:
            self._tick_callback()
        self._instructions_executable += 1
        if self._instructions_executable >= self._instructions_per_update:
            self._instructions_executable = 0
            self._decrement_timer()
            if self._update_callback:
                self._update_callback()

    def _decrement_timer(self) -> None:
        if self._delay_timer:
            self._delay_timer -= 1
        if self._sound_timer:
            self._sound_timer -= 1

    def _execute_instruction(self) -> None:  # noqa: C901, PLR0912, PLR0915
        instruction = (self._bus[self._pc] << 8) | (self._bus[self._pc + 1])
        op = (instruction >> 12) & 0xF
        nnn = instruction & 0xFFF
        nn = instruction & 0xFF
        n = instruction & 0xF
        x = (instruction >> 8) & 0xF
        y = (instruction >> 4) & 0xF
        self._pc += 2

        if instruction == 0x00E0:
            self._instruction_cls()
        elif instruction == 0x00EE:
            self._instruction_rts()
        elif op == 0:
            self._instruction_sys(nnn)
        elif op == 1:
            self._instruction_jump(nnn)
        elif op == 2:
            self._instruction_call(nnn)
        elif op == 3:
            self._instruction_skip_eq_imediate(x, nn)
        elif op == 4:
            self._instruction_skip_ne_imediate(x, nn)
        elif op == 5 and n == 0:
            self._instruction_skip_eq_register(x, y)
        elif op == 6:
            self._instruction_mov_imediate(x, nn)
        elif op == 7:
            self._instruction_add_imediate(x, nn)
        elif op == 8 and n == 0:
            self._instruction_mov_register(x, y)
        elif op == 8 and n == 1:
            self._instruction_or(x, y)
        elif op == 8 and n == 2:
            self._instruction_and(x, y)
        elif op == 8 and n == 3:
            self._instruction_xor(x, y)
        elif op == 8 and n == 4:
            self._instruction_add_register(x, y)
        elif op == 8 and n == 5:
            self._instruction_sub(x, y)
        elif op == 8 and n == 6:
            self._instruction_shr(x, y)
        elif op == 8 and n == 7:
            self._instruction_subb(x, y)
        elif op == 8 and n == 0xE:
            self._instruction_shl(x, y)
        elif op == 9 and n == 0:
            self._instruction_skip_ne_register(x, y)
        elif op == 0xA:
            self._instruction_mov_to_i(nnn)
        elif op == 0xB:
            self._instruction_jump_v0(nnn)
        elif op == 0xC:
            self._instruction_rnd(x, nn)
        elif op == 0xD:
            self._instruction_sprite(x, y, n)
        elif op == 0xE and nn == 0x9E:
            self._instruction_skip_key(x)
        elif op == 0xE and nn == 0xA1:
            self._instruction_skip_nokey(x)
        elif op == 0xF and nn == 0x07:
            self._instruction_mov_from_delay(x)
        elif op == 0xF and nn == 0x0A:
            self._instruction_wait_key(x)
        elif op == 0xF and nn == 0x15:
            self._instruction_mov_to_delay(x)
        elif op == 0xF and nn == 0x18:
            self._instruction_mov_to_sound(x)
        elif op == 0xF and nn == 0x1E:
            self._instruction_add_to_i(x)
        elif op == 0xF and nn == 0x29:
            self._instruction_spritechar(x)
        elif op == 0xF and nn == 0x33:
            self._instruction_movbcd(x)
        elif op == 0xF and nn == 0x55:
            self._instruction_movm_to_i(x)
        elif op == 0xF and nn == 0x65:
            self._instruction_movm_from_i(x)
        else:
            raise RuntimeError('Undefined instruction')

    def _instruction_sys(self, nnn: int, /) -> None:
        raise NotImplementedError(f'Instruction {nnn:04x} not implemented')

    def _instruction_jump(self, nnn: int, /) -> None:
        self._pc = nnn

    def _instruction_jump_v0(self, nnn: int, /) -> None:
        self._pc = nnn + self._v[0]

    def _instruction_skip_eq_imediate(self, x: int, nn: int, /) -> None:
        if self._v[x] == nn:
            self._pc += 2

    def _instruction_skip_eq_register(self, x: int, y: int, /) -> None:
        if self._v[x] == self._v[y]:
            self._pc += 2

    def _instruction_skip_ne_imediate(self, x: int, nn: int, /) -> None:
        if self._v[x] != nn:
            self._pc += 2

    def _instruction_skip_ne_register(self, x: int, y: int, /) -> None:
        if self._v[x] != self._v[y]:
            self._pc += 2

    def _instruction_call(self, nnn: int, /) -> None:
        self._sp += 2
        self._bus[self._sp] = self._pc >> 8
        self._bus[self._sp + 1] = self._pc & 0xFF
        self._pc = nnn

    def _instruction_rts(self) -> None:
        self._pc = (self._bus[self._sp] << 8) | self._bus[self._sp + 1]
        self._sp -= 2

    def _instruction_movm_to_i(self, x: int, /) -> None:
        for i in range(x + 1):
            self._bus[self._i] = self._v[i]
            self._i += 1

    def _instruction_movm_from_i(self, x: int, /) -> None:
        for i in range(x + 1):
            self._v[i] = self._bus[self._i]
            self._i += 1

    def _instruction_mov_imediate(self, x: int, nn: int, /) -> None:
        self._v[x] = nn

    def _instruction_mov_register(self, x: int, y: int, /) -> None:
        self._v[x] = self._v[y]

    def _instruction_and(self, x: int, y: int, /) -> None:
        self._v[x] &= self._v[y]

    def _instruction_or(self, x: int, y: int, /) -> None:
        self._v[x] |= self._v[y]

    def _instruction_xor(self, x: int, y: int, /) -> None:
        self._v[x] ^= self._v[y]

    def _instruction_add_imediate(self, x: int, nn: int, /) -> None:
        self._v[x] = (self._v[x] + nn) & 0xFF

    def _instruction_add_register(self, x: int, y: int, /) -> None:
        total = self._v[x] + self._v[y]
        self._v[x] = total & 0xFF
        self._v[15] = total >> 8

    def _instruction_sub(self, x: int, y: int, /) -> None:
        self._v[15] = int(self._v[x] > self._v[y])
        self._v[x] = (self._v[x] - self._v[y]) & 0xFF

    def _instruction_subb(self, x: int, y: int, /) -> None:
        self._v[15] = int(self._v[y] > self._v[x])
        self._v[x] = (self._v[y] - self._v[x]) & 0xFF

    def _instruction_shr(self, x: int, y: int, /) -> None:
        self._v[15] = self._v[y] & 1
        self._v[x] = self._v[y] >> 1

    def _instruction_shl(self, x: int, y: int, /) -> None:
        self._v[15] = self._v[y] >> 7
        self._v[x] = (self._v[y] << 1) & 0xFF

    def _instruction_cls(self) -> None:
        self._display.clear()

    def _instruction_sprite(self, x: int, y: int, n: int, /) -> None:
        sprite = [self._bus[i] for i in range(self._i, self._i + n)]
        self._v[15] = int(self._display.draw_sprite(self._v[x], self._v[y], sprite))

    def _instruction_spritechar(self, x: int, /) -> None:
        self._i = self._v[x] * 5

    def _instruction_mov_to_i(self, nnn: int, /) -> None:
        self._i = nnn

    def _instruction_add_to_i(self, x: int, /) -> None:
        self._i = (self._i + self._v[x]) & 0xFFF

    def _instruction_skip_key(self, x: int, /) -> None:
        if self._keyboard[Key(self._v[x])]:
            self._pc += 2

    def _instruction_skip_nokey(self, x: int, /) -> None:
        if not self._keyboard[Key(x)]:
            self._pc += 2

    def _instruction_wait_key(self, x: int, /) -> None:
        if self._waiting_keyboard is None:
            self._waiting_keyboard = self._keyboard.next_key_pressed()
        if self._waiting_keyboard.done():
            self._v[x] = int(self._waiting_keyboard.result())
            self._waiting_keyboard = None
        else:
            self._pc -= 2

    def _instruction_mov_from_delay(self, x: int, /) -> None:
        self._v[x] = self._delay_timer

    def _instruction_mov_to_delay(self, x: int, /) -> None:
        self._delay_timer = self._v[x]

    def _instruction_mov_to_sound(self, x: int, /) -> None:
        self._sound_timer = self._v[x]

    def _instruction_rnd(self, x: int, nn: int, /) -> None:
        self._v[x] = randbits(8) & nn

    def _instruction_movbcd(self, x: int, /) -> None:
        value = self._v[x]
        self._bus[self._i + 2] = value % 10
        value //= 10
        self._bus[self._i + 1] = value % 10
        self._bus[self._i] = value // 10
