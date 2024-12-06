# Step 1: Count occurrences of each ASSET_TYPE in all three DataFrames
count_df1 = df1['ASSET_TYPE'].value_counts().reset_index()
count_df1.columns = ['ASSET_TYPE', 'Count_df1']

count_df2 = df2['ASSET_TYPE'].value_counts().reset_index()
count_df2.columns = ['ASSET_TYPE', 'Count_df2']

count_df3 = df3['ASSET_TYPE'].value_counts().reset_index()
count_df3.columns = ['ASSET_TYPE', 'Count_df3']

# Step 2: Merge the counts from all three DataFrames
merged_counts = (
    count_df1
    .merge(count_df2, on='ASSET_TYPE', how='inner')  # Inner join keeps only common ASSET_TYPEs
    .merge(count_df3, on='ASSET_TYPE', how='inner')
)

# Step 3: Calculate the total count across all three DataFrames
merged_counts['Total_Count'] = (
    merged_counts['Count_df1'] + 
    merged_counts['Count_df2'] + 
    merged_counts['Count_df3']
)

# Step 4: Sort by Total_Count in descending order
merged_counts = merged_counts.sort_values(by='Total_Count', ascending=False)

# Step 5: Get the top common ASSET_TYPEs
top_common_assets = merged_counts.head()  # Adjust head(n) for desired number of top assets

# Print result
print(top_common_assets)
