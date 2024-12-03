# Inputs: Product-specific data
products = {
    "bonds": {"makers": 4, "checkers": 3, "maker_time": 6, "checker_time": 4, "percentiles": {"75th": 50, "90th": 70, "95th": 90}},
    "derivatives": {"makers": 3, "checkers": 2, "maker_time": 8, "checker_time": 5, "percentiles": {"75th": 40, "90th": 60, "95th": 80}},
    "equities": {"makers": 5, "checkers": 4, "maker_time": 5, "checker_time": 3, "percentiles": {"75th": 60, "90th": 85, "95th": 100}},
    "funds": {"makers": 2, "checkers": 2, "maker_time": 10, "checker_time": 6, "percentiles": {"75th": 30, "90th": 50, "95th": 70}},
    "structured_products": {"makers": 3, "checkers": 3, "maker_time": 12, "checker_time": 8, "percentiles": {"75th": 20, "90th": 35, "95th": 50}}
}

work_hours_per_person = 8
work_minutes_per_person = work_hours_per_person * 60  # 8 hours in minutes

# Initialize results
results = {}

# Process each product
for product, data in products.items():
    makers_count = data["makers"]
    checkers_count = data["checkers"]
    maker_time_per_trade = data["maker_time"]
    checker_time_per_trade = data["checker_time"]
    percentiles = data["percentiles"]

    product_results = {}
    for key, trades in percentiles.items():
        total_maker_time = trades * maker_time_per_trade
        total_checker_time = trades * checker_time_per_trade

        # Distribute the workload among makers and checkers
        maker_minutes_per_person = total_maker_time / makers_count
        checker_minutes_per_person = total_checker_time / checkers_count

        # Check if workload exceeds 8 hours
        exceeds_makers = maker_minutes_per_person > work_minutes_per_person
        exceeds_checkers = checker_minutes_per_person > work_minutes_per_person

        product_results[key] = {
            "trades": trades,
            "maker_minutes_per_person": maker_minutes_per_person,
            "checker_minutes_per_person": checker_minutes_per_person,
            "exceeds_makers": exceeds_makers,
            "exceeds_checkers": exceeds_checkers,
        }

    results[product] = product_results

# Aggregated threshold calculation
threshold_trades = {}
for trades in range(1, 500):  # Test trade values for aggregation
    total_maker_time = 0
    total_checker_time = 0

    for product, data in products.items():
        makers_count = data["makers"]
        checkers_count = data["checkers"]
        maker_time_per_trade = data["maker_time"]
        checker_time_per_trade = data["checker_time"]

        total_maker_time += trades * maker_time_per_trade
        total_checker_time += trades * checker_time_per_trade

    maker_minutes_per_person = total_maker_time / sum(data["makers"] for data in products.values())
    checker_minutes_per_person = total_checker_time / sum(data["checkers"] for data in products.values())

    if maker_minutes_per_person > work_minutes_per_person or checker_minutes_per_person > work_minutes_per_person:
        threshold_trades = trades
        break

# Display results
import pprint
pprint.pprint(results)
print(f"\nMinimum trades required to exceed 8 hours: {threshold_trades}")
