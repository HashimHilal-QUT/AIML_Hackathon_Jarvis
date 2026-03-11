# rite a program in the file equilateral.py that accepts the lengths of three sides of
# a triangle as inputs. The program output should indicate whether or not the
# triangle is an equilateral triangle.


a = float(input("Enter the length of side a: "))
b = float(input("Enter the length of side b:"))
c = float(input("Enter the length of side c:"))

# Check if all sides are equal
if a == b == c:
    print("The triangle is an equilateral triangle.")
else:
    print("The triangle is not an equilateral triangle.")
# Output the sides for verification
print(f"Sides: a: {a}, b: {b}, c: {c}")
# This program checks if the triangle is equilateral based on user input.
