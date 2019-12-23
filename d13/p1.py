from __future__ import annotations

import asyncio
import itertools
import sys
from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import Callable, Final, Iterator, Literal

HALT = 99


POSITION_MODE = 0
IMMEDIATE_MODE = 1
RELATIVE_MODE = 2

ParamMode = Literal[POSITION_MODE, IMMEDIATE_MODE, RELATIVE_MODE]
OpCode = int


class ParamType(Enum):
    INPUT = auto()
    OUTPUT = auto()


def read_code() -> list[int]:
    with open("d13/input.txt", "r") as f:
        return [int(i) for i in f.read().split(",")]


def parse_op_code(raw_op_code: int,) -> tuple[OpCode, list[ParamMode]]:
    str_op_code = f"{raw_op_code:05}"
    return (
        int(str_op_code[3:]),
        [int(str_op_code[2]), int(str_op_code[1]), int(str_op_code[0])],
    )


SPEC: dict[OpCode, tuple[Callable, list[ParamType]]] = {}


def handler(op_code: OpCode, params: list[ParamType]):
    def wrapper(fn):
        SPEC[op_code] = (fn, params)
        return fn

    return wrapper


@dataclass
class Processor:
    code: list[int]
    inputs: asyncio.Queue
    outputs: asyncio.Queue

    halted: bool = False

    i: int = field(init=False, default=0)
    relative_base: int = field(init=False, default=0)

    def __setitem__(self, index, value):
        try:
            self.code[index] = value
        except IndexError:
            self.code.extend(itertools.repeat(0, index - len(self.code) + 1))
            self.code[index] = value

    def __getitem__(self, index):
        try:
            return self.code[index]
        except IndexError:
            return 0

    def _consume_params(
        self, param_types: list[ParamType], param_modes: list[ParamMode]
    ) -> Iterator[int]:
        params = zip(
            self[self.i + 1 : self.i + len(param_types) + 1], param_types, param_modes,
        )
        self.i += len(param_types) + 1
        for value, param_type, param_mode in params:
            if param_type == ParamType.INPUT:
                if param_mode == POSITION_MODE:
                    yield self[value]
                elif param_mode == RELATIVE_MODE:
                    yield self[self.relative_base + value]
                elif param_mode == IMMEDIATE_MODE:
                    yield value
            else:  # param_type == ParamType.OUTPUT:
                if param_mode == POSITION_MODE:
                    yield value
                elif param_mode == RELATIVE_MODE:
                    yield self.relative_base + value
                elif param_mode == IMMEDIATE_MODE:
                    assert False
                    yield value

    async def run(self):
        while True:
            op_code, param_modes = parse_op_code(self[self.i])
            if op_code == HALT:
                self.halted = True
                return
            handler, param_types = SPEC[op_code]
            params = tuple(self._consume_params(param_types, param_modes))
            await handler(self, *params)

    @handler(1, [ParamType.INPUT, ParamType.INPUT, ParamType.OUTPUT])
    async def add(self, a, b, out):
        self[out] = a + b

    @handler(2, [ParamType.INPUT, ParamType.INPUT, ParamType.OUTPUT])
    async def mul(self, a, b, out):
        self[out] = a * b

    @handler(3, [ParamType.OUTPUT])
    async def input(self, out):
        self[out] = await self.inputs.get()

    @handler(4, [ParamType.INPUT])
    async def output(self, a):
        await self.outputs.put(a)

    @handler(5, [ParamType.INPUT, ParamType.INPUT])
    async def jump_if_true(self, a, b):
        if a != 0:
            self.i = b

    @handler(6, [ParamType.INPUT, ParamType.INPUT])
    async def jump_if_false(self, a, b):
        if a == 0:
            self.i = b

    @handler(7, [ParamType.INPUT, ParamType.INPUT, ParamType.OUTPUT])
    async def less_than(self, a, b, out):
        self[out] = 1 if a < b else 0

    @handler(8, [ParamType.INPUT, ParamType.INPUT, ParamType.OUTPUT])
    async def equals(self, a, b, out):
        self[out] = 1 if a == b else 0

    @handler(9, [ParamType.INPUT])
    async def adjust_relative_base(self, b):
        self.relative_base += b


EMPTY: Final[int] = 0
WALL: Final[int] = 1
BLOCK: Final[int] = 2
HORIZONTAL_PADDLE: Final[int] = 3
BALL: Final[int] = 4


Tile: Literal[EMPTY, WALL, BLOCK, HORIZONTAL_PADDLE, BALL]


@dataclass
class Arcade:
    processer: Processor

    grid: dict[tuple[int, int], Tile] = field(default_factory=dict)

    ball: tuple[int, int] = None
    paddle: tuple[int, int] = None

    def draw(self, coord: tuple[int, int], tile: Tile):
        self.grid[coord] = tile
        if tile == BALL:
            self.ball = coord
        if tile == HORIZONTAL_PADDLE:
            self.paddle = coord

    async def run(self):
        while not (self.processer.halted and self.processer.outputs.empty()):
            changed = False
            while not self.processer.outputs.empty():
                position = (
                    await self.processer.outputs.get(),
                    await self.processer.outputs.get(),
                )
                tile = await self.processer.outputs.get()
                if position == (-1, 0):
                    print(f"Score is {tile}")
                    continue

                self.draw(position, tile)
                changed = True
            if changed:
                display(self.grid)
            else:
                await self.player()
                await asyncio.sleep(0.1)

    async def player(self) -> None:
        if self.ball[0] > self.paddle[0]:
            await self.joystick(1)
        elif self.ball[0] < self.paddle[0]:
            await self.joystick(-1)
        else:
            await self.joystick(0)

    def get_block_tiles(self):
        return len([None for t in self.grid.values() if t == BLOCK])

    async def joystick(self, input: int):
        # print(input)
        await self.processer.inputs.put(input)


def take_input() -> int:
    move = input()
    if move == "l":
        return -1
    elif move == "r":
        return 1
    return 0


def get_display_size(coords: dict[tuple[int, int] : Tile]) -> tuple[int, int]:
    return max(x for x, _ in coords) + 1, max(y for _, y in coords) + 1


def icon(tile: Tile) -> str:
    return {EMPTY: " ", WALL: "W", BLOCK: "B", HORIZONTAL_PADDLE: "P", BALL: "O",}[tile]


def display(coords: dict[tuple[int, int] : Tile]) -> None:
    max_x, max_y = get_display_size(coords)

    print("-" * max_x)
    for y in range(max_y):
        print("".join(icon(coords.get((x, y), EMPTY)) for x in range(max_x)))
    print("-" * max_x)


async def main():
    code = read_code()
    code[0] = 2
    p = Processor(code, asyncio.Queue(), asyncio.Queue())
    arcade = Arcade(p)
    arcade_task = asyncio.gather(p.run(), arcade.run())#, ai(arcade))

    # while True:
    #     await arcade.joystick(
    #         await asyncio.get_running_loop().run_in_executor(None, take_input)
    #     )

    await arcade_task
    # print(arcade.get_block_tiles())


if __name__ == "__main__":
    asyncio.run(main())
