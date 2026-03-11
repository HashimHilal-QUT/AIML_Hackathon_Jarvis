# . Write a program in the file right.py that accepts the lengths of three sides of a
# triangle as inputs. The program output should indicate whether or not the triangle
# is a right triangle. Recall from the Pythagorean theorem that in a right triangle, the
# square of one side equals the sum of the squares of the other two sides.


a = int(input("Enter the length of side a: "))
b = int(input("Enter the length of side b: "))
c = int(input("Enter the length of side c: "))
# Sort the sides to ensure c is the longest side
# Check if the triangle is a right triangle using the Pythagorean theorem
if a < b and a < c:
    
elif b < a and b < c:   
    a, b, c = a, c, b
elif c < a and c < b:
    a, b, c = a, b, c
# Check if the triangle is a right triangle using the Pythagorean theorem

c1 = a**2 == b**2 + c**2
c2 = b**2 == a**2 + c**2
c3 = c**2 == a**2 + b**2

if (c1):
    print("The triangle is a right triangle.")
else:
    print("The triangle is not a right triangle.")
# Output the sides for verification     
print(f"Sides: a: {a}, b: {b}, c: {c}")

