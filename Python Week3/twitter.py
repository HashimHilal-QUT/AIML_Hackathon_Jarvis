


a = input("Enter your message: ")
if len(a) <= 140:
    print("Your message is short enough for Twitter.")
else:
    print("Your message is too long for Twitter.")
#Output the length of messasges for verification
print(f"Message length: {len(a)} characters")