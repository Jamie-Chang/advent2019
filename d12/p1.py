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


def time_step(moons: list[Moon]) -> None:
    for moon1 in moons:
        for moon2 in moons:
            if moon1 == moon2:
                continue

            moon1.apply_gravity(moon2)

    for moon in moons:
        moon.apply_velocity()


def system_energy(moons: list[Moon]) -> int:
    return sum(moon.total_energy for moon in moons)


if __name__ == "__main__":
    moons = get_moons()

    for _ in range(1000):
        time_step(moons)
        # print(moons)

    print(system_energy(moons))

