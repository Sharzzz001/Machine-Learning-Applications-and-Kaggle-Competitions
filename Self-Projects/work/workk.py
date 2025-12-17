import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm

radar_df = df[df["ROC_x"] == "Awaiting Radar approval"].copy()

uti_max_age = (
    radar_df
    .groupby("Unique Eventid", as_index=False)["Age of Roc"]
    .max()
    .rename(columns={"Age of Roc": "Max_Age_Awaiting_Radar"})
)

ages = uti_max_age["Max_Age_Awaiting_Radar"]

mean_age = ages.mean()
median_age = ages.median()
std_age = ages.std()


plt.figure(figsize=(12, 6))

# Histogram (normalized for PDF overlay)
sns.histplot(
    ages,
    bins="auto",
    stat="density",
    color="#4C72B0",
    alpha=0.6,
    edgecolor="black",
    label="UTI Distribution"
)

# Normal distribution curve
x = np.linspace(ages.min(), ages.max(), 300)
pdf = norm.pdf(x, mean_age, std_age)

plt.plot(
    x,
    pdf,
    color="red",
    linewidth=2,
    label="Normal Distribution"
)

# Mean and Median lines
plt.axvline(
    mean_age,
    color="black",
    linestyle="--",
    linewidth=2,
    label=f"Mean = {mean_age:.1f}"
)

plt.axvline(
    median_age,
    color="green",
    linestyle="--",
    linewidth=2,
    label=f"Median = {median_age:.1f}"
)

# Labels & title
plt.xlabel("Age of ROC (Business Days)")
plt.ylabel("Density (UTIs)")
plt.title("Distribution of Max Age for 'Awaiting Radar Approval' ROC")

plt.legend()
plt.tight_layout()
plt.show()


