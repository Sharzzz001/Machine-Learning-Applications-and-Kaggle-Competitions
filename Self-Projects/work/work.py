import pandas as pd

# Inputs: Trade volumes and times for each product
products = {
    "bonds": {"maker_time": 6, "checker_time": 4, "trades": {"average": 60, "min": 40, "max": 100, "75th": 50, "90th": 70, "95th": 90}},
    "derivatives": {"maker_time": 8, "checker_time": 5, "trades": {"average": 50, "min": 30, "max": 80, "75th": 40, "90th": 60, "95th": 80}},
    "equities": {"maker_time": 5, "checker_time": 3, "trades": {"average": 70, "min": 50, "max": 120, "75th": 60, "90th": 85, "95th": 100}},
    "funds": {"maker_time": 10, "checker_time": 6, "trades": {"average": 40, "min": 20, "max": 70, "75th": 30, "90th": 50, "95th": 70}},
    "structured_products": {"maker_time": 12, "checker_time": 8, "trades": {"average": 30, "min": 10, "max": 50, "75th": 20, "90th": 35, "95th": 50}}
}

# Constants
makers = 5
checkers = 2
work_hours_per_person = 8
work_minutes_per_person = work_hours_per_person * 60

# Initialize a list for results
results = []

# Process each product
for product, data in products.items():
    maker_time_per_trade = data["maker_time"]
    checker_time_per_trade = data["checker_time"]
    trade_values = data["trades"]

    for key, trades in trade_values.items():
        total_maker_time = trades * maker_time_per_trade
        total_checker_time = trades * checker_time_per_trade

        # Distribute the workload among makers and checkers
        maker_minutes_per_person = total_maker_time / makers
        checker_minutes_per_person = total_checker_time / checkers

        # Check if workload exceeds 8 hours
        exceeds_makers = maker_minutes_per_person > work_minutes_per_person
        exceeds_checkers = checker_minutes_per_person > work_minutes_per_person

        results.append({
            "Product": product,
            "Metric": key,
            "Trades": trades,
            "Maker Minutes/Person": maker_minutes_per_person,
            "Checker Minutes/Person": checker_minutes_per_person,
            "Exceeds Makers": exceeds_makers,
            "Exceeds Checkers": exceeds_checkers
        })

# Convert results to DataFrame
results_df = pd.DataFrame(results)

# Aggregated threshold calculation
thresholds = []
for trades in range(1, 500):  # Test trade values for aggregation
    total_maker_time = 0
    total_checker_time = 0

    for product, data in products.items():
        maker_time_per_trade = data["maker_time"]
        checker_time_per_trade = data["checker_time"]

        total_maker_time += trades * maker_time_per_trade
        total_checker_time += trades * checker_time_per_trade

    maker_minutes_per_person = total_maker_time / makers
    checker_minutes_per_person = total_checker_time / checkers

    if maker_minutes_per_person > work_minutes_per_person or checker_minutes_per_person > work_minutes_per_person:
        thresholds.append({"Trades": trades, "Maker Minutes/Person": maker_minutes_per_person, "Checker Minutes/Person": checker_minutes_per_person})
        break

threshold_df = pd.DataFrame(thresholds)

# Display results
print("Workload Analysis:")
print(results_df)
print("\nAggregate Threshold:")
print(threshold_df)
