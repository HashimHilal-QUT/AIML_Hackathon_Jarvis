

account_number = int(input("Enter your account number:"))
number = account_number[::3]
check = account_number[3]

if len(account_number) == 4:
    print("Invalid account number.")
else number%check == 0 and account_number > 0 and  len(account_number) == 4:
    print("valid account number.")

################

acc = input("Enter your 4-digit account number: ").strip()

if not (acc.isdigit() and len(acc) == 4):
	print("Invalid account number.")
else:
	first_three = int(acc[:3])
	check_digit = int(acc[3])
	if first_three % 7 == check_digit:
		print("valid account number.")
	else:
		print("Invalid account number.")