# Inputs
makers_count = 5
checkers_count = 3
maker_time_per_trade = 5  # in minutes
checker_time_per_trade = 3  # in minutes
work_hours_per_person = 8
work_minutes_per_person = work_hours_per_person * 60  # 8 hours in minutes

# Percentile values for number of trades
percentiles = {
    "average": 100,  # Example value
    "max": 150,      # Example value
    "75th": 120,     # Example value
    "90th": 140,     # Example value
    "95th": 160      # Example value
}

# Calculate total minutes required for each percentile
results = {}
for key, trades in percentiles.items():
    total_maker_time = trades * maker_time_per_trade
    total_checker_time = trades * checker_time_per_trade
    
    # Distribute the workload among makers and checkers
    maker_minutes_per_person = total_maker_time / makers_count
    checker_minutes_per_person = total_checker_time / checkers_count
    
    # Check if workload exceeds 8 hours
    exceeds_makers = maker_minutes_per_person > work_minutes_per_person
    exceeds_checkers = checker_minutes_per_person > work_minutes_per_person
    
    results[key] = {
        "trades": trades,
        "maker_minutes_per_person": maker_minutes_per_person,
        "checker_minutes_per_person": checker_minutes_per_person,
        "exceeds_makers": exceeds_makers,
        "exceeds_checkers": exceeds_checkers
    }

# Find the minimum number of trades where either makers or checkers exceed 8 hours
threshold_trades = None
for trades in range(1, 500):  # Test trade values
    total_maker_time = trades * maker_time_per_trade
    total_checker_time = trades * checker_time_per_trade
    
    maker_minutes_per_person = total_maker_time / makers_count
    checker_minutes_per_person = total_checker_time / checkers_count
    
    if maker_minutes_per_person > work_minutes_per_person or checker_minutes_per_person > work_minutes_per_person:
        threshold_trades = trades
        break

# Display results
print("Workload Analysis:")
for key, value in results.items():
    print(f"{key.capitalize()} Trades: {value}")

print(f"\nTrades required to exceed 8 hours: {threshold_trades}")
