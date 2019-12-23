from __future__ import annotations

from typing import Iterator


def check_digits(num: int) -> bool:
    # the digits of the digits must be in increasing order
    # and at least two are the same (must be adjacent given)
    digits = f"{num:06}"
    return (
        int(digits[0])
        <= int(digits[1])
        <= int(digits[2])
        <= int(digits[3])
        <= int(digits[4])
        <= int(digits[5])
    ) and check_pairs(digits)
    # and (len(set(digits)) < 6)


def quads(digits: str) -> str:
    yield f'X{digits[:3]}'
    for i in range(len(digits) - 3):
        yield digits[i: i + 4]
    yield f'{digits[-3:]}X'


def check_pairs(digits: str) -> bool:
    current_char = digits[0]
    number = 1
    for q in quads(digits):
        if q[0] != q[1] and q[1] == q[2] and q[2] != q[3]:
            return True

    return False


def generate(start: int, end: int) -> Iterator[int]:
    return (i for i in range(start, end + 1) if check_digits(i))


if __name__ == "__main__":
    total = 0
    for _ in generate(128392, 643281):
        total += 1
    print(total)

