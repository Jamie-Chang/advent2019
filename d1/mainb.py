def get_input():
    with open('input.txt', 'r') as f:
        for line in f:
            yield int(line[:-1])



if __name__ == '__main__':
    total = 0
    for num in get_input():
        while (num := num // 3 - 2) > 0:
            total += num
    print(total)
