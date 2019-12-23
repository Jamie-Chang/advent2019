from __future__ import annotations

import asyncio
import itertools
import sys
from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import AsyncIterator, Callable, Final, Iterator, Literal

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
    with open("d15/input.txt", "r") as f:
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

    def copy(self):
        p = Processor(
            code=self.code.copy(),
            inputs=asyncio.Queue(),
            outputs=asyncio.Queue(),
            halted=self.halted,
        )
        p.i = self.i
        p.relative_base = self.relative_base
        return p

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


NORTH: int = 1
SOUTH: int = 2
WEST: int = 3
EAST: int = 4


def move(coord: tuple[int, int], direction: int) -> tuple[int, int]:
    x, y = coord
    if direction == NORTH:
        coord = x, y - 1
    elif direction == SOUTH:
        coord = x, y + 1
    elif direction == WEST:
        coord = x - 1, y
    elif direction == EAST:
        coord = x + 1, y
    return coord


def opposite(direction: int) -> int:
    if direction == NORTH:
        return SOUTH
    if direction == SOUTH:
        return NORTH
    if direction == WEST:
        return EAST
    if direction == EAST:
        return WEST


@dataclass
class Droid:
    processor: Processor
    coord: tuple[int, int] = (0, 0)
    moves: list[int] = field(default_factory=list)

    def copy(self) -> Droid:
        return Droid(self.processor.copy(), self.coord, self.moves)

    async def move(self, direction: int):

        await self.processor.inputs.put(direction)
        status = await self.processor.outputs.get()

        if status == 0:
            return 0

        self.moves.append(direction)
        self.coord = move(self.coord, direction)

        return status

    async def move_back(self):
        pass


# async def find(droid: Droid) -> int:
#     queue = [droid]
#     visited = {(0, 0)}
#     while queue:
#         droid = queue.pop(0)
#         visited.add(droid.coord)
#         for d in range(1, 5):
#             if move(droid.coord, d) in visited:
#                 continue
#             new_droid = droid.copy()
#             status = await new_droid.move(d)
#             if status == 2:
#                 return new_droid.moves
            
#             if status == 0:
#                 continue

#             queue.append(new_droid)
MOVES = set()
BOARD = {}


async def walk(droid: Droid, direction: int):
    p = droid.processor
    print(droid.coord, direction)
    if (droid.coord, direction) in MOVES:
        return
    await p.inputs.put(direction)
    status = await p.outputs.get()
    MOVES.add((droid.coord, direction))

    if status == 0:
        BOARD[move(droid.coord, direction)] = '#'
    elif status == 1:
        droid.move_(direction)
        BOARD[droid.coord] = '.'
    elif status == 2:
        droid.move_(direction)
        BOARD[droid.coord] = '*'
    
    for d in (NORTH, EAST, SOUTH, WEST):
        await walk(droid, d)


async def main():
    d = Droid((p:= Processor(read_code(), asyncio.Queue(), asyncio.Queue())))
    t = asyncio.create_task(p.run())
    # while True:
    #     direction = int(input())
    #     await p.inputs.put(direction)
    #     status = await p.outputs.get()
    #     if status != 0:
    #         d.move_(direction)
    #     coord = d.coord
    #     print(f"{status = }, {coord = }")
    for direction in (NORTH, EAST, SOUTH, WEST):
        await walk(d, direction)
    print(BOARD)
    await t

    # print(await find(Droid(Processor(read_code(), asyncio.Queue(), asyncio.Queue()))))


if __name__ == "__main__":
    asyncio.run(main())