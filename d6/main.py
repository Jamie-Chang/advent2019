from __future__ import annotations

from collections import defaultdict
from typing import Iterator, Final

COM: Final[str] = "COM"


def read() -> Iterator[tuple[str, str]]:
    with open("d6/input.txt") as f:
        for l in f:
            yield tuple(l.rstrip().split(")"))


def build_tree(orbits: Iterator[tuple[str, str]]) -> dict[str, set[str]]:
    tree: dict[str, set[str]] = defaultdict(set)
    for orbitee, orbiter in orbits:
        tree[orbitee].add(orbiter)
        tree[orbiter].add(orbitee)
    return tree


def count_orbits(tree: dict[str, set[str]], start: str = COM) -> int:
    queue = [(start, 0)]
    total = 0
    while queue:
        planet, orbit_no = queue.pop(0)
        total += orbit_no
        queue.extend((p, orbit_no + 1) for p in tree[planet])
    return total


def count_transfers(tree: dict[str, set[str]], start: str = "YOU") -> int:
    visted = set()
    queue = [(start, 0)]
    total = 0
    while queue:
        planet, orbit_no = queue.pop(0)
        if planet == "SAN":
            return orbit_no - 2
        visted.add(planet)
        queue.extend((p, orbit_no + 1) for p in tree[planet] if p not in visted)
    return total


if __name__ == "__main__":
    tree = build_tree(read())
    print(count_transfers(tree))

