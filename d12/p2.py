from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from parse import compile


@dataclass
class Moon:
    coord: list[int]
    velocity: list[int] = field(default_factory=lambda: [0, 0, 0])

    def apply_gravity(self, moon: Moon) -> None:
        for dimension in range(3):
            if self.coord[dimension] > moon.coord[dimension]:
                self.velocity[dimension] -= 1
            elif self.coord[dimension] < moon.coord[dimension]:
                self.velocity[dimension] += 1

    def apply_velocity(self):
        for dimension in range(3):
            self.coord[dimension] += self.velocity[dimension]

    @property
    def potential_energy(self):
        return sum(abs(c) for c in self.coord)

    @property
    def kinetic_energy(self):
        return sum(abs(v) for v in self.velocity)

    @property
    def total_energy(self):
        return self.potential_energy * self.kinetic_energy

    @property
    def state(self):
        return tuple(self.coord), tuple(self.velocity)


def read_lines() -> Iterator[str]:
    with open("d12/input.txt", "r") as f:
        for line in f:
            yield line.rstrip()


def get_coords() -> Iterator[list[int]]:
    p = compile("<x={x:d}, y={y:d}, z={z:d}>")
    for line in read_lines():
        result = p.parse(line)
        yield [result["x"], result["y"], result["z"]]


def get_moons() -> list[Moon]:
    return [Moon(c) for c in get_coords()]


def get_system_state(moons: list[Moon]):
    return tuple(moon.state for moon in moons)


def time_step(moons: list[Moon]):
    for moon in moons:
        for moon_r in moons:
            if moon_r is moon:
                continue
            moon.apply_gravity(moon_r)

    # total = len(moons)
    # for dimention in range(3):
    #     for i, moon in enumerate(sorted(moons, key=lambda moon: moon.coord[dimention])):
    #         moon.velocity[dimention] += total - 1 - i * 2

    for moon in moons:
        moon.apply_velocity()

    return get_system_state(moons)


def system_energy(moons: list[Moon]) -> int:
    return sum(moon.total_energy for moon in moons)


if __name__ == "__main__":
    moons = get_moons()
    states = {get_system_state(moons)}
    count = 0
    while True:
        count += 1
        if (state := time_step(moons)) in states:
            print(count)
            break

        states.add(state)

