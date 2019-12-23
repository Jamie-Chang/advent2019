import math
from typing import Dict, Final, Tuple

from parse import compile


p = compile("{quantity:d} {chemical}")

Formula = Tuple[str, Tuple[int, Dict[str, int]]]
Formulae = Dict[str, Tuple[int, Dict[str, int]]]

ore: Final[str] = "ORE"
fuel: Final[str] = "FUEL"


def read_lines():
    with open("d14/input.txt", "r") as f:
        for line in f:
            yield line.rstrip()


def read_formula(line: str) -> Formula:
    ingredients, produce = line.split(" => ")

    pp = p.parse(produce)
    ingredients_dict = {}
    for ingredient in ingredients.split(", "):
        i = p.parse(ingredient)
        ingredients_dict[i["chemical"]] = i["quantity"]

    return (pp["chemical"], (pp["quantity"], ingredients_dict))


def get_formulae() -> Formulae:
    formulae = {}
    for line in read_lines():
        k, v = read_formula(line)
        formulae[k] = v
    return formulae


def get_cost(formulae: Formulae, target: str, target_amount: int):
    spares = {}
    queue = [(target, target_amount)]
    cost = 0
    while queue:
        target, target_amount = queue.pop(0)

        if target == ore:
            cost += target_amount
            continue
        
        if spares.get(target, 0) >= target_amount:
            spares[target] -= target_amount
            continue
        target_amount -= spares.pop(target, 0)
        
        produce_amount, ingredients = formulae[target]
        times = math.ceil(target_amount / produce_amount)
        extra = produce_amount * times - target_amount
        spares.setdefault(target, 0)
        spares[target] += extra
        for c, a in ingredients.items():
            queue.append((c, a * times))
    return cost


def iterative_approx(formulae: Formulae, target: str, target_cost: int) -> int:
    target_amount = 1
    while True:
        cost = get_cost(formulae, target, target_amount)
        new_target_amount = int(target_cost / cost * target_amount)
        if new_target_amount == target_amount:
            return target_amount
        target_amount = new_target_amount


if __name__ == "__main__":
    print(iterative_approx(get_formulae(), fuel, 1_000_000_000_000))
