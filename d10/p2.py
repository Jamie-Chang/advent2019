from __future__ import annotations

from collections import defaultdict
from itertools import zip_longest
from math import gcd, inf
from typing import Iterator, Tuple

Coord = Tuple[int, int]
Phase = Tuple[int, int]

STATION = (37, 25)


def get_coords() -> Iterator[Coord]:
    with open("d10/input.txt", "r") as f:
        for j, l in enumerate(f):
            for i, c in enumerate(l.rstrip()):
                if c == "#":
                    yield i, j



def get_phase(coord1: Coord, coord2: Coord) -> Phase:

    x1, y1 = coord1
    x2, y2 = coord2

    dx = x2 - x1
    dy = y2 - y1

    if not dx:
        return (1 if y2 > y1 else -1, 0)

    if not dy:
        return (0, 1 if x2 > x1 else -1)

    g = gcd(dx, dy)
    return dy // g, dx // g




def numeric_phase(phase: Phase) -> tuple[int, float]:
    dy, dx = phase
    if dy < 0 and dx >= 0:
        return (0, -dx / dy)
    
    if dy >= 0 and dx > 0:
        return (1, dy / dx)
    
    if dy > 0 and dx <= 0:
        return (3, -dx / dy)
    
    if dy <= 0 and dx < 0:
        return (4, dy / dx)

    print(phase)

def get_distance(coord1: Coord, coord2: Coord) -> int:
    x1, y1 = coord1
    x2, y2 = coord2
    return (y2 - y1) ** 2 + (x2 - x1) ** 2


def get_destroyed():
    group_by_phase = defaultdict(list)
    for coord in get_coords():
        if coord == STATION:
            continue
        group_by_phase[get_phase(STATION, coord)].append(coord)

    for coords in group_by_phase.values():
        coords.sort(key=lambda c: get_distance(STATION, c))

    phase_order = sorted(group_by_phase, key=numeric_phase)

    zipped = zip_longest(*(group_by_phase[phase] for phase in phase_order))
    for coords in zipped:
        for coord in coords:
            if coord is not None:
                yield coord


if __name__ == "__main__":
    destroyed = list(get_destroyed())
    for i in (200,):
        print(i, destroyed[i - 1])

