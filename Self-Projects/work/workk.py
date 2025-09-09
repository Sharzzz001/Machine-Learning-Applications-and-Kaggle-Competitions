import pandas as pd
import numpy as np

def calculate_status_ageing(df: pd.DataFrame) -> pd.DataFrame:
    df['File_Date'] = pd.to_datetime(df['File_Date'])
    df['Trigger_Date'] = pd.to_datetime(df['Trigger_Date'])
    
    # Unique request identifier
    df['Request_ID'] = (
        df['Account_ID'].astype(str) + "_" +
        df['Review_Type'].astype(str) + "_" +
        df['Trigger_Date'].dt.strftime("%Y-%m-%d")
    )
    
    results = []
    
    for req_id, g in df.groupby('Request_ID'):
        g = g.sort_values('File_Date').copy()
        
        # ✅ Collapse duplicates: keep last record per File_Date
        g = g.groupby('File_Date').last().reset_index()
        
        # Create per-request business day calendar
        all_bdays = pd.date_range(g['File_Date'].min(), g['File_Date'].max(), freq="B")
        
        # Align to business days
        g = g.set_index('File_Date').reindex(all_bdays).sort_index()
        g.index.name = 'File_Date'
        
        # Forward fill statuses and static columns
        g[['Doc_Status','Screening_Status']] = g[['Doc_Status','Screening_Status']].ffill()
        for col in ['Account_ID','Trigger_Date','Review_Type']:
            g[col] = g[col].ffill()
        
        # Total ageing (business days in queue)
        total_ageing = len(g)
        
        # Snapshot count = actual days we had a file
        total_snapshots = g['Doc_Status'].notna().sum()
        
        # Latest statuses
        latest_doc = g['Doc_Status'].iloc[-1]
        latest_screen = g['Screening_Status'].iloc[-1]
        
        # Latest status ageing
        latest_doc_age = (g['Doc_Status'][::-1] == latest_doc).cumprod().sum()
        latest_screen_age = (g['Screening_Status'][::-1] == latest_screen).cumprod().sum()
        
        # Per-status ageing
        doc_counts = g.groupby('Doc_Status').size().to_dict()
        screen_counts = g.groupby('Screening_Status').size().to_dict()
        
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
        
        for k,v in doc_counts.items():
            row[f'Doc_Ageing_{k}'] = v
        for k,v in screen_counts.items():
            row[f'Screen_Ageing_{k}'] = v
        
        results.append(row)
    
    return pd.DataFrame(results)