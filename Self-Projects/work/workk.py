def calculate_remaining_entertainment(necessary_spends, entertainment_spent, total_per_diem=2112, declarable_ratio=0.66):
    """
    Calculates how much more you can safely spend on entertainment.

    Returns:
    - Max total entertainment allowed
    - Remaining entertainment you can still spend
    """

    # 1. Hard cap: max total allowed entertainment (based on 66% rule)
    max_total_spend_by_66 = necessary_spends / declarable_ratio
    max_entertainment_by_66 = max_total_spend_by_66 - necessary_spends

    # 2. Cap based on 33% of total per diem
    max_entertainment_by_33 = total_per_diem * (1 - declarable_ratio)

    # 3. Cap based on remaining money
    remaining_budget = total_per_diem - (necessary_spends + entertainment_spent)

    # 4. Take the minimum of all three constraints
    remaining_entertainment = min(
        max_entertainment_by_66 - entertainment_spent,
        max_entertainment_by_33 - entertainment_spent,
        remaining_budget
    )

    # Clamp to 0 if over budget
    remaining_entertainment = max(0, round(remaining_entertainment, 2))
    max_entertainment_allowed = min(max_entertainment_by_66, max_entertainment_by_33, total_per_diem - necessary_spends)

    return round(max_entertainment_allowed, 2), remaining_entertainment


# ==== Interactive Prompt ====
try:
    necessary_spends = float(input("Enter your total F&B/laundry/etc. spend so far (SGD): "))
    entertainment_spent = float(input("Enter your entertainment spend so far (SGD): "))

    max_entertainment, remaining = calculate_remaining_entertainment(necessary_spends, entertainment_spent)

    print(f"\n✅ Max total entertainment allowed: SGD {max_entertainment}")
    print(f"💡 Remaining entertainment you can still spend: SGD {remaining}")
except ValueError:
    print("⚠️ Please enter valid numbers.")