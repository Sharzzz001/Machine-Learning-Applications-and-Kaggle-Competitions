import re
import pandas as pd
import numpy as np

def extract_and_sum_numbers(text):
    if pd.isna(text):
        return 0

    numbers = re.findall(r"\d+", str(text))
    return sum(map(int, numbers))
    
df["Total_Securities"] = df["Securities"].apply(extract_and_sum_numbers)
df["Pending_Securities_Count"] = df["Pending securities"].apply(extract_and_sum_numbers)


df["Securities_Completed"] = (
    df["Total_Securities"] - df["Pending_Securities_Count"]
)

df["Securities_Completion_%"] = np.where(
    df["Total_Securities"] > 0,
    (df["Securities_Completed"] / df["Total_Securities"]) * 100,
    np.nan
)

