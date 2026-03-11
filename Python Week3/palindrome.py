myString = "python"


# for i in range(len(myString) - 1, -1, -1):
#     print(myString[i], end="")

# print()

reversedString = ""
for char in myString:
    reversedString = char + reversedString
print(reversedString)



