import pandas as pd

# Load your original Excel file
df = pd.read_excel("your_file.xlsx")

# Pick the columns to mask
columns_to_mask = ['CustomerName', 'Email', 'AccountID']  # example

# Store mappings for reversibility
mask_maps = {}

for col in columns_to_mask:
    unique_vals = df[col].dropna().unique()
    
    # Create a mapping: each unique value gets a fake label
    mapping = {orig: f"{col}_MASKED_{i+1:04d}" for i, orig in enumerate(unique_vals)}
    
    # Apply mapping
    df[col] = df[col].map(mapping)
    
    # Save mapping for reverse unmasking
    mask_maps[col] = mapping

# Save the masked file
df.to_excel("masked_output.xlsx", index=False)

# Optionally save the mappings to JSON for unmasking later
import json

with open("mask_mappings.json", "w") as f:
    json.dump(mask_maps, f)