from __future__ import annotations

from collections import defaultdict
from math import gcd
from typing import Dict, Iterator, Tuple

Coord = Tuple[int, int]
Phase = Tuple[int, int]

PhaseMap = Dict[Coord, Dict[Coord, Phase]]
DistanceMap = Dict[Coord, Dict[Coord, int]]


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
    return dx // g, dy // g


def get_distance(coord1: Coord, coord2: Coord) -> int:
    x1, y1 = coord1
    x2, y2 = coord2
    return (y2 - y1) ** 2 + (x2 - x1) ** 2


def generate_maps(coords: list[Coord]) -> Tuple[PhaseMap, DistanceMap]:
    phase_map = defaultdict(dict)
    distance_map = defaultdict(dict)
    while coords:
        try:
            coord1 = coords.pop()
        except IndexError:
            break
        for coord2 in coords:
            distance = get_distance(coord1, coord2)
            phase_map[coord1][coord2] = get_phase(coord1, coord2)
            phase_map[coord2][coord1] = get_phase(coord2, coord1)
            distance_map[coord1][coord2] = distance
            distance_map[coord2][coord1] = distance
    return phase_map, distance_map


def get_detectable(phases: Dict[Coord, Fraction]) -> int:
    return len({phase for phase in phases.values()})


if __name__ == "__main__":
    phase_map, _ = generate_maps(list(get_coords()))
    # print(phase_map[2, 2])
    # print(get_detectable(phase_map[11, 13]))
    # print(
    #     sorted(list(
    #         ((c, get_detectable(ps)) for c, ps in phase_map.items())#, key=lambda i: i[1]
    #     ))
    # )
    print(
        max(
            ((c, get_detectable(ps)) for c, ps in phase_map.items()), key=lambda i: i[1]
        )
    )
