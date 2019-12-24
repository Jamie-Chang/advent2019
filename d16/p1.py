from pathlib import Path
from typing import Callable, Iterable, Iterator, List
from itertools import chain, cycle, islice, repeat

import numpy as np


BASE_PATTERN = [0, 1, 0, -1]


def read_lines() -> Iterator[str]:
    with (Path(__file__).parent / "input.txt").open("r") as f:
        for line in f:
            yield line.rstrip()


def get_inputs() -> Iterator[int]:
    line = list(read_lines())[0]
    for i in line:
        yield int(i)


def repeat_each(pattern, repeats: int):
    return chain(*map(lambda i: repeat(i, repeats), pattern))


def generate_pattern(base: Iterable[int], repeats: int, length: int) -> Iterator[int]:
    """Generate the pattern as specified by the algorithm.

    Example:
        >>> list(generate_pattern([0, 1, 0, -1], 2, 15))
        [0, 1, 1, 0, 0, -1, -1, 0, 0, 1, 1, 0, 0, -1, -1]
    """
    return islice(cycle(repeat_each(base, repeats)), 1, length + 1)


def create_filter_matrix(length: int) -> np.array:
    return np.array(
        [list(generate_pattern(BASE_PATTERN, i + 1, length)) for i in range(length)]
    )


def create_input_vector() -> np.array:
    return np.array(list(get_inputs()))


def create_last_digit_filter() -> Callable:
    return np.vectorize(lambda i: abs(i) % 10)


def perform_fft(iterations: int) -> np.array:
    vector = create_input_vector()
    filter_matrix = create_filter_matrix(len(vector))
    last_digit_filter = create_last_digit_filter()
    for _ in range(iterations):
        vector = last_digit_filter(filter_matrix @ vector)
    return vector


# print(list(generate_pattern(2, 10)))
print(perform_fft(100)[:8])