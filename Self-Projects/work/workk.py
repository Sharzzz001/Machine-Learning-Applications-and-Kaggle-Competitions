LAST_1M_START = "2025-11-09"
LAST_1M_END   = "2025-12-08"

PREV_3M_START = "2025-08-09"
PREV_3M_END   = "2025-11-08"

radar_df = df[df["ROC_x"] == "Awaiting Radar approval"].copy()
radar_df["Business Date"] = pd.to_datetime(radar_df["Business Date"])

def build_period_df(df, start_date, end_date):
    period_df = df[
        (df["Business Date"] >= start_date) &
        (df["Business Date"] <= end_date)
    ]

    return (
        period_df
        .groupby("Unique Eventid", as_index=False)["Age of Roc"]
        .max()
        .rename(columns={"Age of Roc": "Max_Age"})
    )

last_1m_df = build_period_df(radar_df, LAST_1M_START, LAST_1M_END)
prev_3m_df = build_period_df(radar_df, PREV_3M_START, PREV_3M_END)

summary = pd.DataFrame({
    "Period": ["Last 1 Month", "Previous 3 Months"],
    "UTI_Count": [len(last_1m_df), len(prev_3m_df)],
    "Mean_Age": [last_1m_df["Max_Age"].mean(), prev_3m_df["Max_Age"].mean()],
    "Median_Age": [last_1m_df["Max_Age"].median(), prev_3m_df["Max_Age"].median()]
})

summary




plt.figure(figsize=(12,6))

sns.histplot(
    prev_3m_df["Max_Age"],
    bins="auto",
    stat="density",
    alpha=0.5,
    label="Previous 3 Months"
)

sns.histplot(
    last_1m_df["Max_Age"],
    bins="auto",
    stat="density",
    alpha=0.5,
    label="Last 1 Month"
)

plt.axvline(last_1m_df["Max_Age"].mean(), linestyle="--", label="Last 1M Mean")
plt.axvline(prev_3m_df["Max_Age"].mean(), linestyle="--", label="Prev 3M Mean")

plt.xlabel("Age of ROC (Business Days)")
plt.ylabel("Density")
plt.title("Awaiting Radar Approval – Age Distribution Comparison")
plt.legend()
plt.tight_layout()
plt.show()





fig, axes = plt.subplots(1, 2, figsize=(14,6), sharex=True, sharey=True)

sns.histplot(
    prev_3m_df["Max_Age"],
    bins="auto",
    ax=axes[0]
)
axes[0].set_title("Previous 3 Months")
axes[0].axvline(prev_3m_df["Max_Age"].mean(), linestyle="--")

sns.histplot(
    last_1m_df["Max_Age"],
    bins="auto",
    ax=axes[1]
)
axes[1].set_title("Last 1 Month")
axes[1].axvline(last_1m_df["Max_Age"].mean(), linestyle="--")

for ax in axes:
    ax.set_xlabel("Age of ROC (Business Days)")
    ax.set_ylabel("UTI Count")

plt.tight_layout()
plt.show()





plot_df = pd.concat([
    last_1m_df.assign(Period="Last 1 Month"),
    prev_3m_df.assign(Period="Previous 3 Months")
])

plt.figure(figsize=(10,6))
sns.violinplot(x="Period", y="Max_Age", data=plot_df, inner="quartile")
sns.boxplot(x="Period", y="Max_Age", data=plot_df, width=0.2)

plt.ylabel("Age of ROC (Business Days)")
plt.title("Awaiting Radar Approval – Aging Spread Comparison")
plt.tight_layout()
plt.show()





current_mean = last_1m_df["Max_Age"].mean()
previous_mean = prev_3m_df["Max_Age"].mean()

target_mean = min(previous_mean, 10)  # configurable

n = len(last_1m_df)

current_total_age = last_1m_df["Max_Age"].sum()
target_total_age = target_mean * n

reduction_required = current_total_age - target_total_age
avg_reduction_per_uti = reduction_required / n

flip_metrics = {
    "Current Avg Age": round(current_mean, 2),
    "Previous Avg Age": round(previous_mean, 2),
    "Target Avg Age": round(target_mean, 2),
    "UTI Count": n,
    "Total Aging Reduction Needed (Days)": round(reduction_required, 1),
    "Avg Reduction per UTI (Days)": round(avg_reduction_per_uti, 2)
}

flip_metrics



