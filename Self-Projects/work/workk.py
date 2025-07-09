import pyodbc
import pandas as pd

# --- Config ---
access_db_path = r"C:\path\to\your\database.accdb"  # Change this
table_name = "YourTableName"                        # Change this
parquet_output_path = r"C:\path\to\output.parquet"  # Change this

# --- Connection String (for Access .accdb) ---
conn_str = (
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    f"DBQ={access_db_path};"
)

# --- Read Table from Access ---
with pyodbc.connect(conn_str) as conn:
    query = f"SELECT * FROM [{table_name}]"
    df = pd.read_sql(query, conn)

# --- Save to Parquet ---
df.to_parquet(parquet_output_path, engine="pyarrow", index=False)

print(f"✅ Exported {len(df)} rows from '{table_name}' to '{parquet_output_path}'")


import pandas as pd
import hashlib
from cryptography.fernet import Fernet

# Set up a reversible encryption key — save this securely!
key = Fernet.generate_key()
cipher = Fernet(key)

# Save this key to a file for unmasking later
with open("masking_key.key", "wb") as f:
    f.write(key)

def encrypt_value(val):
    if pd.isnull(val): return val
    return cipher.encrypt(str(val).encode()).decode()

def decrypt_value(val):
    if pd.isnull(val): return val
    return cipher.decrypt(val.encode()).decode()
    
# Load your Excel
df = pd.read_excel("original_data.xlsx")

# Define sensitive columns
sensitive_cols = ['Name', 'Email']

# Mask them
for col in sensitive_cols:
    df[col] = df[col].apply(encrypt_value)

# Optionally obfuscate Salary but keep ratios
df['Salary'] = df['Salary'] * 1.2  # or use encryption if you want

# Save masked version
df.to_excel("masked_data.xlsx", index=False)

# Load key again
with open("masking_key.key", "rb") as f:
    key = f.read()

cipher = Fernet(key)

# Load transformed file
masked_df = pd.read_excel("masked_transformed.xlsx")

# Decrypt
for col in sensitive_cols:
    masked_df[col] = masked_df[col].apply(decrypt_value)