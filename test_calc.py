from system_control import calculate

def test_calc():
    test_cases = [
        "what is 5 + 5",
        "calculate 10 * 2",
        "how much is 100 divided by 4",
        "what's 50 minus 10",
        "please compute 2^3",
        "5 plus 5"
    ]
    
    for case in test_cases:
        res = calculate(case)
        print(f"Input: '{case}' -> Output: {res}")

if __name__ == "__main__":
    test_calc()
