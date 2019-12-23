from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Literal, Callable, Iterator

HALT = 99


POSITION_MODE = 0
IMMEDIATE_MODE = 1

ParamMode = Literal[POSITION_MODE, IMMEDIATE_MODE]
OpCode = int


class ParamType(Enum):
    VALUE = auto()
    LOCATION = auto()


class Unknown(Exception):
    def __init__(self, op_code: int):
        self.op_code = op_code
        super().__init__()


def read_code() -> list[int]:
    with open("d5/input.txt", "r") as f:
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
class Processer:
    code: list[int]

    i: int = field(init=False, default=0)

    def _consume_params(
        self, param_types: list[ParamType], param_modes: list[ParamMode]
    ) -> Iterator[int]:
        params = zip(
            self.code[self.i + 1 : self.i + len(param_types) + 1],
            param_types,
            param_modes,
        )
        self.i += len(param_types) + 1
        for value, param_type, param_mode in params:
            if param_type == ParamType.VALUE:
                if param_mode == POSITION_MODE:
                    yield self.code[value]
                    continue
            yield value

    def run(self):
        while self.i < len(self.code):
            op_code, param_modes = parse_op_code(self.code[self.i])
            if op_code == HALT:
                return
            handler, param_types = SPEC[op_code]
            params = tuple(self._consume_params(param_types, param_modes))
            handler(self, *params)

    @handler(1, [ParamType.VALUE, ParamType.VALUE, ParamType.LOCATION])
    def add(self, a, b, loc):
        self.code[loc] = a + b

    @handler(2, [ParamType.VALUE, ParamType.VALUE, ParamType.LOCATION])
    def mul(self, a, b, loc):
        self.code[loc] = a * b

    @handler(3, [ParamType.LOCATION])
    def input(self, loc):
        self.code[loc] = int(input())

    @handler(4, [ParamType.LOCATION])
    def output(self, loc):
        print(self.code[loc])

    @handler(5, [ParamType.VALUE, ParamType.VALUE])
    def jump_if_true(self, a, b):
        if a != 0:
            self.i = b

    @handler(6, [ParamType.VALUE, ParamType.VALUE])
    def jump_if_false(self, a, b):
        if a == 0:
            self.i = b

    @handler(7, [ParamType.VALUE, ParamType.VALUE, ParamType.LOCATION])
    def less_than(self, a, b, loc):
        self.code[loc] = 1 if a < b else 0

    @handler(8, [ParamType.VALUE, ParamType.VALUE, ParamType.LOCATION])
    def equals(self, a, b, loc):
        self.code[loc] = 1 if a == b else 0


if __name__ == "__main__":
    code = read_code()
    Processer(code).run()
