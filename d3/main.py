from __future__ import annotations

from typing import Iterator, Tuple, List

Wire = List[Tuple[str, int]]
Coord = Tuple[int, int]


def read_code() -> Iterator[Wire]:
    with open("input.txt", "r") as f:
        for l in f:
            line = l[:-1]
            yield [(i[0], int(i[1:])) for i in line.split(",")]


def traverse(wire: Wire) -> Iterator[tuple[Coord, int]]:
    x, y = 0, 0
    wire_distance = 0
    for direction, distance in wire:
        for _ in range(distance):
            wire_distance += 1
            if direction == "U":
                y += 1
            elif direction == "D":
                y -= 1
            elif direction == "L":
                x -= 1
            elif direction == "R":
                x += 1

            yield (x, y), wire_distance


def get_man_dist(coord: Coord):
    return abs(coord[0]) + abs(coord[1])


if __name__ == "__main__":
    w1, w2 = read_code()
    w1_nodes = dict(traverse(w1))
    print(
        min(
            ((c, d1 + d2) for c, d2 in traverse(w2) if (d1 := w1_nodes.get(c))),
            key=lambda p: p[1],
        )
    )

