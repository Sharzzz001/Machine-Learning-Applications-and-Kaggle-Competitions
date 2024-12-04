import pandas as pd
import numpy as np

# Example DataFrame (replace this with your actual data)
# The DataFrame should have columns: 'Date', 'bonds', 'derivatives', 'equities', 'funds', 'structured_products'
data = {
    "Date": pd.date_range(start="2024-01-01", periods=10),
    "bonds": np.random.randint(10, 100, size=10),
    "derivatives": np.random.randint(5, 50, size=10),
    "equities": np.random.randint(20, 150, size=10),
    "funds": np.random.randint(5, 40, size=10),
    "structured_products": np.random.randint(1, 30, size=10),
}
df = pd.DataFrame(data)

# Define processing times for each product type
products = {
    "bonds": {"maker_time": 6, "checker_time": 4},
    "derivatives": {"maker_time": 8, "checker_time": 5},
    "equities": {"maker_time": 5, "checker_time": 3},
    "funds": {"maker_time": 10, "checker_time": 6},
    "structured_products": {"maker_time": 12, "checker_time": 8},
}

# Initialize columns for maker and checker times
df["Maker Time"] = 0
df["Checker Time"] = 0

# Calculate maker and checker times for each product and day
for product, times in products.items():
    maker_time = times["maker_time"]
    checker_time = times["checker_time"]
    df["Maker Time"] += df[product] * maker_time
    df["Checker Time"] += df[product] * checker_time

# Calculate daily statistics
statistics = {
    "Metric": ["Average", "Min", "Max", "75th Percentile", "90th Percentile", "95th Percentile"],
    "Maker Time (Minutes)": [
        df["Maker Time"].mean(),
        df["Maker Time"].min(),
        df["Maker Time"].max(),
        np.percentile(df["Maker Time"], 75),
        np.percentile(df["Maker Time"], 90),
        np.percentile(df["Maker Time"], 95),
    ],
    "Checker Time (Minutes)": [
        df["Checker Time"].mean(),
        df["Checker Time"].min(),
        df["Checker Time"].max(),
        np.percentile(df["Checker Time"], 75),
        np.percentile(df["Checker Time"], 90),
        np.percentile(df["Checker Time"], 95),
    ],
}

# Create a DataFrame for the statistics
stats_df = pd.DataFrame(statistics)

# Display results
print("Daily Maker and Checker Times:")
print(df)
print("\nSummary Statistics:")
print(stats_df)
