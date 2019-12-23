from __future__ import annotations

ADD = 1
MUL = 2
HALT = 99


class Unknown(Exception):
    def __init__(self, op_code: int):
        self.op_code = op_code
        super().__init__()


def read_code() -> list[int]:
    with open("input.txt", "r") as f:
        return [int(i) for i in f.read().split(',')]


def parse_instructions(code: list[int]):
    for i in range(0, len(code), 4):
        if code[i] == HALT:
            return
        yield code[i:i + 4]


def process_instruction(
    instruction: list[int], code: list[int]
) -> None:
    op_code = instruction[0]
    if op_code == ADD:
        code[instruction[3]] = code[instruction[1]] + code[instruction[2]]
    elif op_code == MUL:
        code[instruction[3]] = code[instruction[1]] * code[instruction[2]]
    else:
        raise Unknown(op_code)


def processer(code: list[int]) -> int:
    for instruction in parse_instructions(code):
        process_instruction(instruction, code)
    
    return code[0]


def generate_input() -> tuple[int, int]:
    for i in range(100):
        for j in range(100):
            yield i, j

if __name__ == '__main__':
    print(code := read_code())
    output = 19690720
    for noun, verb in generate_input():
        current_code = code.copy()
        current_code[1] = noun
        current_code[2] = verb
        if processer(current_code) == output:
            print(100 * noun + verb)
            break