from __future__ import annotations

import asyncio
import itertools
import sys
from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from pathlib import Path
from typing import AsyncIterator, Callable, Final, Iterator, List, Literal, Tuple

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
    with (Path(__file__).parent / "input.txt").open("r") as f:
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
    started: asyncio.locks.Event = field(default_factory=asyncio.locks.Event)

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
        self.started.set()
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


@dataclass
class Camera:
    processor: Processor
    path: set[tuple[int, int]] = field(init=False, default_factory=set)
    
    async def consume(self):
        char_list = []
        x, y = 0, 0
        while not self.processor.outputs.empty():
            value = await self.processor.outputs.get()
            char_list.append(val := str(chr(value)))
            if val == '\n':
                x = 0
                y += 1
                continue
            
            if val in ('#', '<', '>', '^', 'v'):
                self.path.add((x, y))
            x += 1

        print(''.join(char_list))
    
    def get_intersections(self):
        for x, y in self.path:
            neighbours = {
                (x, y + 1),
                (x, y - 1),
                (x + 1, y),
                (x - 1, y),
            }
            if neighbours <= self.path:
                yield (x, y)


async def main():
    t = asyncio.create_task((processor := Processor(read_code())).run())
    await processor.started.wait()
    await (camera := Camera(processor)).consume()
    print(list(camera.get_intersections()))
    print(sum(x * y for x, y in camera.get_intersections()))
        
    await t


if __name__ == "__main__":
    asyncio.run(main())
