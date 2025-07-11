def calculate_remaining_entertainment(necessary_spends, entertainment_spent, total_per_diem=2112, declarable_ratio=0.66):
    """
    Calculates how much more you can spend on entertainment.

    Parameters:
    - necessary_spends (float): Total legit expenses (F&B, laundry, etc.)
    - entertainment_spent (float): Amount already spent on entertainment
    - total_per_diem (float): Total allowance for the trip (default = 2112)
    - declarable_ratio (float): Minimum % of spend that must be billable (default = 0.66)

    Returns:
    - Max total entertainment allowed
    - Remaining entertainment you can still spend
    """
    max_non_declarable_spend = total_per_diem * (1 - declarable_ratio)

    # Based on 66% rule: total_spend <= necessary / 0.66
    max_total_spend = necessary_spends / declarable_ratio
    max_entertainment_spend = max_total_spend - necessary_spends

    # Cap by 33% rule (non-declarable portion)
    max_entertainment_spend = min(max_entertainment_spend, max_non_declarable_spend)

    # Remaining entertainment budget
    remaining_entertainment = max(0, round(max_entertainment_spend - entertainment_spent, 2))

    return round(max_entertainment_spend, 2), remaining_entertainment


# ==== Interactive Prompt ====
try:
    necessary_spends = float(input("Enter your total F&B/laundry/etc. spend so far (SGD): "))
    entertainment_spent = float(input("Enter your entertainment spend so far (SGD): "))

    max_entertainment, remaining = calculate_remaining_entertainment(necessary_spends, entertainment_spent)

    print(f"\n✅ Max entertainment allowed: SGD {max_entertainment}")
    print(f"💡 Remaining entertainment you can still spend: SGD {remaining}")
except ValueError:
    print("⚠️ Please enter valid numbers.")