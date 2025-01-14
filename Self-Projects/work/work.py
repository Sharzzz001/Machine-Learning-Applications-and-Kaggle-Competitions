import os
import pandas as pd
from datetime import datetime

# Specify the folder to scan
folder_path = "path_to_your_folder"

# List to store file data
file_data = []

# Scan the folder for .xlsx files
for file in os.listdir(folder_path):
    if file.endswith(".xlsx"):
        file_path = os.path.join(folder_path, file)
        created_time = os.path.getctime(file_path)  # Get the creation time
        created_time = datetime.fromtimestamp(created_time)  # Convert to datetime
        file_data.append({"Filename": file, "Created Time": created_time})

# Create a DataFrame
df = pd.DataFrame(file_data)

# Display the DataFrame
print(df)

# Save to a CSV file if needed
df.to_csv("file_details.csv", index=False)