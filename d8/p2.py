from __future__ import annotations

from typing import Iterator


def _split(string: str, split_size: int) -> Iterator[str]:
    for i in range(0, len(string), split_size):
        yield string[i : i + split_size]


def _create_layer(string: str, width: int, height: int) -> list[list[int]]:
    return [
        [(int(c)) for c in string[r * width : (r + 1) * width]] for r in range(height)
    ]


def generate_input() -> Iterator[list[list[int]]]:
    with open("d8/input.txt", "r") as f:
        for chunk in _split(f.read(), 25 * 6):
            yield _create_layer(chunk, 25, 6)


def count(layer: list[list[int]], pixel: int) -> int:
    total = 0
    for row in layer:
        for cell in row:
            if cell == pixel:
                total += 1
    return total


def cover(a, b):
    """`a` covers `b`"""
    for r, row in enumerate(b):
        for c, back in enumerate(row):
            front = a[r][c]
            if front == 2:
                a[r][c] = back


def print_layer(layer: list[list[int]]) -> None:
    for row in layer:
        print("".join("X" if i else " " for i in row))


if __name__ == "__main__":
    current_layer = None
    for layer in generate_input():
        if current_layer is None:
            current_layer = layer
            continue

        cover(current_layer, layer)
    print_layer(current_layer)

