# Ask the user for the filename
filename = input("Enter the filename: ")

try:
    with open(filename, 'r') as file:
        lines = file.readlines()  # Read all lines into a list
        line_count = len(lines)   # Count the number of lines
    print(f"Number of lines in {filename}: {line_count}")
except FileNotFoundError:
    print(f"File '{filename}' not found.")
