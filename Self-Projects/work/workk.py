def calculate_entertainment_allowance(necessary_spends, total_per_diem=2112, declarable_ratio=0.66):
    """
    necessary_spends: total F&B/laundry/etc. expenses over the trip (in SGD)
    total_per_diem: total allowance (default: 2112)
    declarable_ratio: % that must be covered by receipts (default: 66%)
    
    Returns: max entertainment allowance within rules
    """
    max_non_declarable_spend = total_per_diem * (1 - declarable_ratio)
    
    # Total spent = necessary + entertainment
    # To stay within 66% declarable rule:
    # necessary_spends >= (total_spent) * 0.66
    # => total_spent <= necessary_spends / 0.66

    max_total_spend = necessary_spends / declarable_ratio
    max_entertainment_spend = max_total_spend - necessary_spends

    # Also cap at total_per_diem * 0.33
    max_entertainment_spend = min(max_entertainment_spend, max_non_declarable_spend)

    return round(max_entertainment_spend, 2)


# Example usage
necessary_spends = float(input("Enter your total F&B/laundry/etc. spend (SGD): "))
entertainment_allowance = calculate_entertainment_allowance(necessary_spends)
print(f"\n💡 You can safely spend up to SGD {entertainment_allowance} on entertainment without exceeding your 33% cap.")