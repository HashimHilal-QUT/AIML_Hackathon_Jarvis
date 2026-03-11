import random

sum = 0


f = open("integers.txt", "r+")
for i in range(100):
    number = random.randint(1, 1000)
    f.write(f"{str(number)}\n")

# with open("integers.txt", "r") as f:
    for line in f:
        sum += int(line.strip())
print(f"The sum of the integers in 'integers.txt' is: {sum}")