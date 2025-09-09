import pandas as pd
import numpy as np

def calculate_status_ageing(df: pd.DataFrame) -> pd.DataFrame:
    # --- Step 1: Ensure correct dtypes ---
    df['File_Date'] = pd.to_datetime(df['File_Date'])
    df['Trigger_Date'] = pd.to_datetime(df['Trigger_Date'])
    
    # --- Step 2: Build unique request id ---
    df['Request_ID'] = (
        df['Account_ID'].astype(str) + "_" +
        df['Review_Type'].astype(str) + "_" +
        df['Trigger_Date'].dt.strftime("%Y-%m-%d")
    )
    
    # --- Step 3: Create business day calendar ---
    all_bdays = pd.date_range(df['File_Date'].min(), df['File_Date'].max(), freq="B")
    
    # --- Step 4: Prepare results list ---
    results = []
    
    # --- Step 5: Process per unique request ---
    for req_id, g in df.groupby('Request_ID'):
        g = g.sort_values('File_Date').copy()
        
        # Align to business days
        g = g.set_index('File_Date').reindex(all_bdays).sort_index()
        
        # Forward fill to carry last known status
        g[['Doc_Status','Screening_Status']] = g[['Doc_Status','Screening_Status']].ffill()
        
        # Fill static columns forward (Account_ID, Trigger_Date, Review_Type etc.)
        for col in ['Account_ID','Trigger_Date','Review_Type']:
            g[col] = g[col].ffill()
        
        # Compute total ageing and snapshots
        total_ageing = len(g)  # total business days in queue
        total_snapshots = g['Doc_Status'].notna().sum()  # number of actual snapshot days
        
        # Get latest values
        latest_doc = g['Doc_Status'].iloc[-1]
        latest_screen = g['Screening_Status'].iloc[-1]
        
        # Compute latest status ageing
        latest_doc_age = (g['Doc_Status'][::-1] == latest_doc).cumprod().sum()
        latest_screen_age = (g['Screening_Status'][::-1] == latest_screen).cumprod().sum()
        
        # --- Step 6: Per-status ageing ---
        doc_counts = g.groupby('Doc_Status').size().to_dict()
        screen_counts = g.groupby('Screening_Status').size().to_dict()
        
        # Build row dict
        row = {
            'Request_ID': req_id,
            'Account_ID': g['Account_ID'].iloc[-1],
            'Trigger_Date': g['Trigger_Date'].iloc[-1],
            'Review_Type': g['Review_Type'].iloc[-1],
            'Total_Ageing': total_ageing,
            'Total_Snapshots': total_snapshots,
            'Latest_Doc_Status': latest_doc,
            'Latest_Doc_Ageing': latest_doc_age,
            'Latest_Screening_Status': latest_screen,
            'Latest_Screening_Ageing': latest_screen_age
        }
        
        # Add dynamic status ageing
        for k,v in doc_counts.items():
            row[f'Doc_Ageing_{k}'] = v
        for k,v in screen_counts.items():
            row[f'Screen_Ageing_{k}'] = v
        
        results.append(row)
    
    # --- Step 7: Return as DataFrame ---
    final_df = pd.DataFrame(results)
    return final_df


# ------------------------------
# Example usage:
# df = pd.read_excel("your_file.xlsx")
# final_df = calculate_status_ageing(df)
# final_df.to_excel("final_ageing_output.xlsx", index=False)