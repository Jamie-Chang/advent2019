if __name__ == '__main__':
    with open('input.txt', 'r') as f:
        print(sum(int(line[:-1]) // 3 - 2 for line in f))
