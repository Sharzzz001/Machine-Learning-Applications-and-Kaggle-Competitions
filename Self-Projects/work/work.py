import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Example data
data = {
    'Date': pd.date_range(start='2024-01-01', periods=186, freq='D'),
    'Bonds': [100] * 186, 'Derivatives': [50] * 186,
    'Equities': [75] * 186, 'Funds': [30] * 186,
    'Structured Products': [20] * 186
}
df = pd.DataFrame(data)

# Time taken per trade (minutes)
maker_time = {'Bonds': 5, 'Derivatives': 7, 'Equities': 6, 'Funds': 8, 'Structured Products': 10}
checker_time = {'Bonds': 3, 'Derivatives': 4, 'Equities': 5, 'Funds': 6, 'Structured Products': 8}

# Makers and Checkers Count
makers_count = 5
checkers_count = 3
total_maker_capacity = makers_count * 480  # Total daily maker capacity in minutes
total_checker_capacity = checkers_count * 480  # Total daily checker capacity in minutes

# Calculate workload separately for makers and checkers
for product in ['Bonds', 'Derivatives', 'Equities', 'Funds', 'Structured Products']:
    df[f'{product}_Maker_Time'] = df[product] * maker_time[product]
    df[f'{product}_Checker_Time'] = df[product] * checker_time[product]

# Sum up maker and checker times
df['Total Maker Time'] = df[[f'{product}_Maker_Time' for product in ['Bonds', 'Derivatives', 'Equities', 'Funds', 'Structured Products']]].sum(axis=1)
df['Total Checker Time'] = df[[f'{product}_Checker_Time' for product in ['Bonds', 'Derivatives', 'Equities', 'Funds', 'Structured Products']]].sum(axis=1)

# Total time (makers + checkers)
df['Total Time'] = df['Total Maker Time'] + df['Total Checker Time']

# Identify capacity breaches
df['Exceeds Maker Capacity'] = df['Total Maker Time'] > total_maker_capacity
df['Exceeds Checker Capacity'] = df['Total Checker Time'] > total_checker_capacity

# Forecast trade volumes
forecast_dfs = []
for product in ['Bonds', 'Derivatives', 'Equities', 'Funds', 'Structured Products']:
    model = ExponentialSmoothing(df[product], trend='add', seasonal='add', seasonal_periods=30)
    fit = model.fit()
    forecast = fit.forecast(30)  # Forecast 30 days ahead
    forecast_dfs.append(pd.DataFrame({'Date': pd.date_range(start=df['Date'].iloc[-1] + pd.Timedelta(days=1), periods=30),
                                       f'{product}_Forecast': forecast}))

forecast_df = pd.concat(forecast_dfs, axis=1)
forecast_df = forecast_df.loc[:, ~forecast_df.columns.duplicated()]  # Remove duplicate Date columns

# Calculate forecasted workload separately for makers and checkers
for product in ['Bonds', 'Derivatives', 'Equities', 'Funds', 'Structured Products']:
    forecast_df[f'{product}_Maker_Time_Forecast'] = forecast_df[f'{product}_Forecast'] * maker_time[product]
    forecast_df[f'{product}_Checker_Time_Forecast'] = forecast_df[f'{product}_Forecast'] * checker_time[product]

# Sum up forecasted times
forecast_df['Total Maker Time Forecast'] = forecast_df[[f'{product}_Maker_Time_Forecast' for product in ['Bonds', 'Derivatives', 'Equities', 'Funds', 'Structured Products']]].sum(axis=1)
forecast_df['Total Checker Time Forecast'] = forecast_df[[f'{product}_Checker_Time_Forecast' for product in ['Bonds', 'Derivatives', 'Equities', 'Funds', 'Structured Products']]].sum(axis=1)
forecast_df['Total Time Forecast'] = forecast_df['Total Maker Time Forecast'] + forecast_df['Total Checker Time Forecast']

# Identify forecasted capacity breaches
forecast_df['Exceeds Maker Capacity Forecast'] = forecast_df['Total Maker Time Forecast'] > total_maker_capacity
forecast_df['Exceeds Checker Capacity Forecast'] = forecast_df['Total Checker Time Forecast'] > total_checker_capacity

# Display results
print(df[['Date', 'Total Maker Time', 'Total Checker Time', 'Total Time', 'Exceeds Maker Capacity', 'Exceeds Checker Capacity']])
print(forecast_df[['Date', 'Total Maker Time Forecast', 'Total Checker Time Forecast', 'Total Time Forecast', 'Exceeds Maker Capacity Forecast', 'Exceeds Checker Capacity Forecast']])