import pandas as pd
from datetime import datetime, timedelta


# ============================================================
# 0. CONFIG – UPDATE THESE TO MATCH YOUR RR_MERGED COLUMNS
# ============================================================

COL_REVIEW_TYPE   = "Review Type"
COL_STATUS_CORP   = "StatusCorpInd"
COL_DUE_DATE      = "Due Date"
COL_COMPLETION    = "Completion Date"
COL_FINAL_STATUS  = "Final Status"              # final merged status (doc+ns+sow)
COL_SOW_CONS      = "Consolidated SOW Status"   # consolidated SOW status

# If your names differ (e.g. "FinalStatus" or "Consolidated_SOW_Status"),
# just change the strings above.


# ============================================================
# 1. DATE HELPERS
# ============================================================

def get_month_bounds(as_of_date: datetime):
    """
    Given an as_of_date (e.g. 2025-12-14), return:
    - month_start: 1st of that month
    - month_end:   last day of that month
    - next_month_start: 1st of the next month
    """
    as_of = pd.to_datetime(as_of_date).normalize()
    month_start = as_of.replace(day=1)

    if as_of.month == 12:
        next_month_start = as_of.replace(year=as_of.year + 1, month=1, day=1)
    else:
        next_month_start = as_of.replace(month=as_of.month + 1, day=1)

    month_end = next_month_start - timedelta(days=1)
    return month_start, month_end, next_month_start


# ============================================================
# 2. BASE FILTER – APPLIED TO BOTH <30 AND >=30 BUCKETS
# ============================================================

def base_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Common filtering:
      - Review Type should NOT contain 'Client Updates' or 'Special Accounts'
      - StatusCorpInd should NOT contain 'Cancelled'
    """
    df = df.copy()

    # Ensure string operations work even with NaN
    df[COL_REVIEW_TYPE] = df[COL_REVIEW_TYPE].astype(str)
    df[COL_STATUS_CORP] = df[COL_STATUS_CORP].astype(str)

    mask_review = ~df[COL_REVIEW_TYPE].str.contains(
        "Client Updates|Special Accounts", case=False, na=False
    )

    mask_status = ~df[COL_STATUS_CORP].str.contains(
        "Cancelled", case=False, na=False
    )

    return df[mask_review & mask_status]


# ============================================================
# 3. SPLIT INTO <30 AND >=30 BUCKETS
# ============================================================

def split_le_ge(df: pd.DataFrame, as_of_date: datetime):
    """
    Returns two dataframes: df_le30, df_ge30

    Shared completion logic (for BOTH buckets):
      - Completion Date is either:
          * blank (NaT) OR
          * any date in the same month as 'as_of_date'

    LE30 (< 30 days overdue) logic:
      - Due Date <= end of this month

    GE30 (>= 30 days overdue) logic:
      - Due Date >= start of next month
    """
    df = df.copy()

    df[COL_DUE_DATE] = pd.to_datetime(df[COL_DUE_DATE], errors="coerce")
    df[COL_COMPLETION] = pd.to_datetime(df[COL_COMPLETION], errors="coerce")

    month_start, month_end, next_month_start = get_month_bounds(as_of_date)

    df_base = base_filter(df)

    # Completion condition used for both buckets
    cond_completion = df_base[COL_COMPLETION].isna() | (
        (df_base[COL_COMPLETION] >= month_start) &
        (df_base[COL_COMPLETION] <= month_end)
    )

    # LE30: Due Date <= month_end
    cond_due_le = df_base[COL_DUE_DATE] <= month_end
    df_le30 = df_base[cond_due_le & cond_completion]

    # GE30: Due Date >= next_month_start
    cond_due_ge = df_base[COL_DUE_DATE] >= next_month_start
    df_ge30 = df_base[cond_due_ge & cond_completion]

    # Optional sanity check: ensure we didn't create extra rows
    assert len(df_le30) + len(df_ge30) <= len(df_base), \
        "LE+GE rows exceed base population – check filters."

    return df_le30, df_ge30


# ============================================================
# 4. CATEGORY RULES (a–g)
# ============================================================

def count_category(df: pd.DataFrame, category: str) -> int:
    """
    Count rows in df that belong to category a–g.

    a - StatusCorpInd is 'Pending SM Approval' or 'Pending Attestations'
    b - StatusCorpInd is 'Pending Cancellations'
    c - Final Status is 'Pending FO'
    d - Final Status is 'Pending FCC'
    e - Final Status is 'Pending BM'
    f - Final Status is 'Pending CDD'
    g - Consolidated SOW Status is CAC / EDD
    """
    if df.empty:
        return 0

    # Ensure we can do string operations safely
    df_loc = df.copy()
    df_loc[COL_STATUS_CORP]  = df_loc[COL_STATUS_CORP].astype(str)
    df_loc[COL_FINAL_STATUS] = df_loc[COL_FINAL_STATUS].astype(str)
    df_loc[COL_SOW_CONS]     = df_loc[COL_SOW_CONS].astype(str)

    if category == "a":
        return df_loc[COL_STATUS_CORP].str.strip().isin([
            "Pending SM Approval",
            "Pending SM Aprroval",   # include typo variant
            "Pending Attestations",
        ]).sum()

    if category == "b":
        return df_loc[COL_STATUS_CORP].str.strip().eq("Pending Cancellations").sum()

    if category == "c":
        return df_loc[COL_FINAL_STATUS].str.strip().eq("Pending FO").sum()

    if category == "d":
        return df_loc[COL_FINAL_STATUS].str.strip().eq("Pending FCC").sum()

    if category == "e":
        return df_loc[COL_FINAL_STATUS].str.strip().eq("Pending BM").sum()

    if category == "f":
        return df_loc[COL_FINAL_STATUS].str.strip().eq("Pending CDD").sum()

    if category == "g":
        # SOW status is CAC / EDD
        return df_loc[COL_SOW_CONS].str.strip().isin(["CAC", "EDD"]).sum()

    return 0


# ============================================================
# 5. BUILD THE SUMMARY TABLE DATAFRAME
# ============================================================

def build_rr_summary(rr_merged: pd.DataFrame, as_of_date: datetime) -> pd.DataFrame:
    """
    Creates a dataframe shaped like your Excel table:

    - Rows (a)–(g): categories with <30 and >=30 counts
    - Then total resolved, unresolved, total volume
    """
    df_le30, df_ge30 = split_le_ge(rr_merged, as_of_date)

    labels = {
        "a": "(a) Pending Final FO Attestations",
        "b": "(b) Cancellation/closures in progress",
        "c": "(c) Pending FO Follow-Ups",
        "d": "(d) Pending FCC / MLRO",
        "e": "(e) Pending BM",
        "f": "(f) Pending CDD",
        "g": "(g) Pending CAC",
    }

    rows = []
    counts_le = {}
    counts_ge = {}

    for cat, label in labels.items():
        le = count_category(df_le30, cat)
        ge = count_category(df_ge30, cat)
        counts_le[cat] = le
        counts_ge[cat] = ge
        rows.append([label, le, ge])

    # Build main table
    summary = pd.DataFrame(
        rows,
        columns=[
            "Breakdown by Status As of Month End",
            "< 30 days overdue",
            ">= 30 days overdue",
        ],
    )

    # Totals:
    # Total resolved = cases in (a) + (b) (both buckets)
    total_resolved = (
        counts_le.get("a", 0) + counts_ge.get("a", 0) +
        counts_le.get("b", 0) + counts_ge.get("b", 0)
    )

    total_overdue = len(df_le30) + len(df_ge30)
    total_unresolved = total_overdue - total_resolved

    # Blank row
    summary.loc[len(summary)] = ["", "", ""]

    # Totals in >=30 column like your screenshot
    summary.loc[len(summary)] = [
        "Total Resolved Overdue RR Cases - (a) + (b)",
        "",
        total_resolved,
    ]
    summary.loc[len(summary)] = [
        "Total Un-Resolved RR Cases",
        "",
        total_unresolved,
    ]
    summary.loc[len(summary)] = [
        "Total Volume of Overdue RR Cases",
        "",
        total_overdue,
    ]

    return summary


# ============================================================
# 6. WRITE TO EXCEL IN YOUR LAYOUT
# ============================================================

def write_rr_summary_to_excel(rr_merged: pd.DataFrame,
                              output_path: str,
                              as_of_date: datetime):
    """
    Writes the summary table to Excel in roughly the same layout as your screenshot.
    """
    summary = build_rr_summary(rr_merged, as_of_date)

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        sheet_name = "Month-end Summary"
        # Start the main table a few rows down for headings
        summary.to_excel(writer, sheet_name=sheet_name, index=False, startrow=4)

        workbook  = writer.book
        worksheet = writer.sheets[sheet_name]

        # Top line
        worksheet.write(0, 0, "Month-end Cutoff time - 10pm SGT")

        # Header lines above table
        worksheet.write(2, 0, "Breakdown by Status As of Month End")
        worksheet.write(2, 1, "Breakdown by Days Overdue As Of Month End")
        worksheet.write(3, 1, "< 30 days overdue")
        worksheet.write(3, 2, ">= 30 days overdue")

        # Column widths
        worksheet.set_column("A:A", 45)
        worksheet.set_column("B:C", 20)


# ============================================================
# 7. EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    # rr_merged = ...  # load / build your rr_merged dataframe here

    # Example: run for "today" or a specific month-end
    as_of = datetime.today()            # or datetime(2025, 12, 14) etc.
    output_file = "RR_month_end_summary.xlsx"

    # write_rr_summary_to_excel(rr_merged, output_file, as_of)
    # print("Summary written to:", output_file)
    pass