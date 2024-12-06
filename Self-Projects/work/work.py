# Step 1: Sort each DataFrame by Count and Proportion
df1_sorted = df1.sort_values(by=['Count', 'Proportion'], ascending=[False, False])
df2_sorted = df2.sort_values(by=['Count', 'Proportion'], ascending=[False, False])
df3_sorted = df3.sort_values(by=['Count', 'Proportion'], ascending=[False, False])

# Step 2: Merge the sorted DataFrames on ASSET_TYPE
merged_df = (
    df1_sorted[['ASSET_TYPE', 'Count', 'Proportion']]
    .rename(columns={'Count': 'Count_df1', 'Proportion': 'Proportion_df1'})
    .merge(
        df2_sorted[['ASSET_TYPE', 'Count', 'Proportion']]
        .rename(columns={'Count': 'Count_df2', 'Proportion': 'Proportion_df2'}),
        on='ASSET_TYPE',
        how='inner'
    )
    .merge(
        df3_sorted[['ASSET_TYPE', 'Count', 'Proportion']]
        .rename(columns={'Count': 'Count_df3', 'Proportion': 'Proportion_df3'}),
        on='ASSET_TYPE',
        how='inner'
    )
)

# Step 3: Add a total count column for overall comparison
merged_df['Total_Count'] = merged_df['Count_df1'] + merged_df['Count_df2'] + merged_df['Count_df3']

# Step 4: Sort the merged DataFrame by Total_Count, Count, and Proportion
merged_df = merged_df.sort_values(by=['Total_Count', 'Count_df1', 'Count_df2', 'Count_df3'], ascending=False)

# Print the top common assets
print(merged_df)
