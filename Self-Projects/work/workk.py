import pandas as pd
import hashlib

# Example: load data
df = pd.read_csv("abc_taxonomy.csv")

# Fixed secret salt (store securely, do NOT share with AI)
SALT = "internal_secret_salt_v1"

def anonymize_name(name: str) -> str:
    if pd.isna(name):
        return None
    key = f"{SALT}_{name.strip().lower()}"
    return "EMP_" + hashlib.sha256(key.encode()).hexdigest()[:10]

df["employee_id"] = df["employee_name"].apply(anonymize_name)

# Drop original PII
df = df.drop(columns=["employee_name"])

df.to_csv("abc_taxonomy_anonymized.csv", index=False)



df["task_path"] = (
    df["level_0"].fillna("") + " | " +
    df["level_1"].fillna("") + " | " +
    df["level_2"].fillna("") + " | " +
    df["level_3"].fillna("") + " | " +
    df["level_4"].fillna("") + " | " +
    df["level_5"].fillna("")
)

analysis_df = df[[
    "region",
    "cost_centre",
    "level_2",
    "task_path",
    "percentage_value"
]]

You are a process mining and AI use-case discovery expert in financial services operations.

You are given task hierarchies from an ABC taxonomy.
Each row represents a unit of work with a hierarchical task path.

Goal:
Identify use cases that are semantically common across DIFFERENT Level 2 processes.

Instructions:
1. Ignore employee-level or effort allocation details.
2. Focus on task intent and activity similarity.
3. Group tasks that represent the same underlying use case, even if wording differs.
4. For each identified common use case, provide:
   - Use case name
   - Description
   - Level 2 processes where it appears
   - Example task paths
   - Why it is suitable (or not) for AI / automation

Here is the data:
<PASTE anonymized task_path + level_2 rows here>

