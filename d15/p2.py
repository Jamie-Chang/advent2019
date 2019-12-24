from __future__ import annotations

import asyncio
import itertools
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import AsyncIterator, Callable, Final, Iterator, List, Literal, Tuple

OXYGEN = [
    4,
    4,
    2,
    2,
    2,
    2,
    3,
    3,
    1,
    1,
    3,
    3,
    1,
    1,
    3,
    3,
    2,
    2,
    2,
    2,
    4,
    4,
    2,
    2,
    4,
    4,
    4,
    4,
    4,
    4,
    1,
    1,
    4,
    4,
    1,
    1,
    3,
    3,
    1,
    1,
    4,
    4,
    4,
    4,
    4,
    4,
    2,
    2,
    4,
    4,
    1,
    1,
    1,
    1,
    4,
    4,
    4,
    4,
    2,
    2,
    2,
    2,
    4,
    4,
    2,
    2,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    2,
    2,
    3,
    3,
    3,
    3,
    2,
    2,
    3,
    3,
    3,
    3,
    2,
    2,
    3,
    3,
    1,
    1,
    3,
    3,
    3,
    3,
    2,
    2,
    2,
    2,
    2,
    2,
    3,
    3,
    1,
    1,
    3,
    3,
    1,
    1,
    3,
    3,
    2,
    2,
    2,
    2,
    4,
    4,
    2,
    2,
    4,
    4,
    2,
    2,
    4,
    4,
    1,
    1,
    4,
    4,
    4,
    4,
    2,
    2,
    4,
    4,
    4,
    4,
    4,
    4,
    1,
    1,
    3,
    3,
    3,
    3,
    1,
    1,
    4,
    4,
    1,
    1,
    4,
    4,
    1,
    1,
    4,
    4,
    4,
    4,
    1,
    1,
    4,
    4,
    1,
    1,
    4,
    4,
    4,
    4,
    2,
    2,
    3,
    3,
    2,
    2,
    4,
    4,
    2,
    2,
    2,
    2,
    4,
    4,
    2,
    2,
    2,
    2,
    3,
    3,
    1,
    1,
    3,
    3,
    3,
    3,
    2,
    2,
    3,
    3,
    3,
    3,
    1,
    1,
    4,
    4,
    1,
    1,
    3,
    3,
    1,
    1,
    4,
    4,
    4,
    4,
    4,
    4,
    2,
    2,
    3,
    3,
]

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
class BaseProcessor:
    code: list[int]
    inputs: asyncio.Queue = field(default_factory=asyncio.Queue)
    outputs: asyncio.Queue = field(default_factory=asyncio.Queue)

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


class Processor(BaseProcessor):
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


def calculate_coord(directions: list[int]) -> tuple[int, int]:
    coord = (0, 0)
    for direction in directions:
        coord = move(coord, direction)
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

    async def move(self, direction: int):
        # print(f"Move from {self.coord = } in {direction = }")
        await self.processor.inputs.put(direction)
        status = await self.processor.outputs.get()

        if status == 0:
            return 0

        self.coord = move(self.coord, direction)

        return status

    @asynccontextmanager
    async def search(self, direction: int):
        """Same as move, but returns to previous location."""
        status = await self.move(direction)
        yield status
        if status != 0:  # Not blocked
            await self.move(opposite(direction))


async def move_to_oxygen(droid: Droid) -> None:
    print("Moving to OXYGEN position")
    for move in OXYGEN:
        await droid.move(move)


async def get_depth(droid: Droid) -> int:
    print("Getting the maximum distance from starting point")
    depth = 370
    nodes = 0
    while True:
        print(f"Trying depth {depth}")
        visited = set()
        for d in range(1, 5):
            await traverse(droid, d, visited, max_depth=depth)
        
        if nodes == (nodes := len(visited)):
            return depth - 1
        
        depth += 1



async def traverse(droid: Droid, direction: int, visited: set[tuple[int, int]], max_depth: int):
    if max_depth == 0:
        return
    async with droid.search(direction) as status:
        if droid.coord in visited:
            return 0

        visited.add(droid.coord)

        if status == 0:
            return 0

        # Recurse
        for d in range(1, 5):
            await traverse(droid, d, visited, max_depth -1)
        
        
    
async def main():
    droid = Droid((p := Processor(read_code())))
    t = asyncio.create_task(p.run())
    await move_to_oxygen(droid)
    print(await get_depth(droid))
    await t


if __name__ == "__main__":
    asyncio.run(main())
