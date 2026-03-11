
# If the student does not meet either of the qualification criteria, display Reject


marks = float(input("Enter your marks : "))
admission_test_score = float(input("Enter your admission test score: "))

if (marks >= 3.0 and admission_test_score >= 60) or (marks < 3.0 and admission_test_score >=80):
    print("Accept the student")
else:
    print(("Reject the student"))