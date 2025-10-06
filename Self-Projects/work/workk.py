import pandas as pd
import re

# ---------- READ INPUT FILES ----------
nts_df = pd.read_excel("NTS.xlsx")
nts_df["Account Number"] = nts_df["Account Number"].astype(str)

active_df = pd.read_excel("Active Blocked Accs_3 Oct.xlsx")
dla_df = pd.read_excel("dla.xlsx", sheet_name="Sheet1")
dla_df["Account Number"] = dla_df["Account Number"].astype(str)

# ---------- CLEANING ----------
active_df = active_df[active_df["Number"].notna()]
ffill = [
    "Root / Location / Team / Salesperson / Contracting Partner",
    "Number",
    "Reference currency",
    "Domicile",
    "Nationality",
    "Remark",
]
active_df[ffill] = active_df[ffill].ffill()
active_df["Remark"] = active_df["Remark"].fillna("")
active_df = active_df.dropna(subset=["Number"]).copy()

df = active_df.copy()
if "Number" in df.columns and "Account" not in df.columns:
    df.rename(columns={"Number": "Account"}, inplace=True)
if (
    "Root / Location / Team / Salesperson / Contracting Partner" in df.columns
    and "Account Name" not in df.columns
):
    df.rename(
        columns={
            "Root / Location / Team / Salesperson / Contracting Partner": "Account Name"
        },
        inplace=True,
    )
df = df[df["Account"].notna()].copy()

# find notes column (first containing 'note')
note_cols = [c for c in df.columns if "note" in c.lower()]
note_col = note_cols[0] if note_cols else "Note Block BP Status"
df["Account"] = df["Account"].astype(str)


# ---------- NORMALIZE REMARK ----------
def normalize_remark(r):
    if pd.isna(r):
        return r
    s = str(r).strip()
    low = s.lower()
    if low.startswith("dormant"):
        return "Dormant"
    if "total block" in low or "total blocking" in low:
        return "Total Blocking"
    if "transfer" in low and "block" in low:
        return "Transfer Blocking"
    return s


df["Remark"] = df["Remark"].apply(normalize_remark)


# ---------- COMBINE NOTES ----------
def combine_notes(series: pd.Series) -> str:
    texts = [str(x).strip() for x in series.dropna().astype(str)]
    texts = [t for t in texts if t]
    seen = set()
    out = []
    for t in texts:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return " || ".join(out)


# canonical account subtitle
subtitle_map = (
    df.groupby("Account", sort=False)["Account Name"]
    .apply(lambda s: s.dropna().astype(str).iloc[0] if len(s.dropna()) > 0 else "")
    .reset_index()
    .rename(columns={"Account Name": "Account_name"})
)

agg = (
    df.groupby("Account", sort=False)
    .agg({"Remark": lambda x: sorted(set(x.dropna().astype(str))), note_col: combine_notes})
    .reset_index()
    .rename(columns={note_col: "Notes"})
)
agg = agg.merge(subtitle_map, on="Account", how="left")
agg["Account_name"] = agg["Account_name"].fillna("")
agg["RemarkCombo"] = agg["Remark"].apply(lambda lst: " + ".join(lst) if lst else "(No Remark)")

# ---------- FLAGS ----------
nts_accounts = nts_df["Account Number"].astype(str).unique()
dla_accounts = dla_df["Account Number"].astype(str).unique()


def is_nonclient_fn(acc):
    s = str(acc).strip()
    return s.startswith(("3", "4", "5"))


agg["is_dormant"] = agg["Remark"].apply(lambda r: len(r) == 1 and str(r[0]) == "Dormant")
agg["is_uc"] = agg["Account_name"].astype(str).str.contains(r"\[UC", case=False, na=False)
agg["is_dla"] = agg["Account"].isin(dla_accounts)
agg["is_nonclient"] = agg["Account"].apply(is_nonclient_fn)
agg["is_nts"] = agg["Account"].isin(nts_accounts)

# counts
dormant_count = int(agg.loc[agg["is_dormant"], "Account"].nunique())
uc_count = int(agg.loc[agg["is_uc"], "Account"].nunique())
dla_count = int(agg.loc[agg["is_dla"], "Account"].nunique())
nonclient_count = int(agg.loc[agg["is_nonclient"], "Account"].nunique())
nts_count = int(agg.loc[agg["is_nts"], "Account"].nunique())

# ---------- EXCLUSION ----------
mask_exclude = agg["is_dormant"] | agg["is_uc"] | agg["is_dla"] | agg["is_nonclient"]
agg_cat = agg.loc[~mask_exclude].copy()

# ---------- KEYWORD MAP (FLAT) ----------
keyword_map = {
    "Overdue RR": ["overdue rr"],
    "IRPQ Attestation": ["irpq attestation", "irpa"],
    "Doc deficiency": ["doc deficiency"],
    "Physical document": ["physical document"],
    "Deceased": ["deceased", "death", "demise"],
    "Bankruptcy": ["bankruptcy", "chap 11"],
    "Court Hearing": ["court", "legal"],
    "FCC/CAC": ["cac"],
    "Sanction": ["sanction"],
    "Address Proof": ["address proof"],
    "Initial funding": ["initial funding"],
    "Expired document": ["expired document"],
    "India Domiciled Client": ["india domiciled client"],
    "T Alerts": ["tm alert"],
}


def categories_for_account(row):
    # If NTS → force category as NTS
    if row["is_nts"]:
        return ["NTS"]

    reason_text = str(row["Notes"]).lower().strip()
    if reason_text == "" or reason_text == "nan":
        return ["Blank"]
    matches = []
    for cat_name, kw_list in keyword_map.items():
        for kw in kw_list:
            if kw.lower() in reason_text:
                matches.append(cat_name)
                break
    if not matches:
        matches = ["Uncategorised"]
    seen = set()
    out = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


agg_cat["Categories"] = agg_cat.apply(categories_for_account, axis=1)

# ---------- EXPLODE ----------
exploded = agg_cat.explode("Categories").dropna(subset=["Categories"]).rename(
    columns={"Categories": "Category"}
)

exploded = exploded[
    [
        "Account",
        "RemarkCombo",
        "Category",
        "Notes",
        "is_dormant",
        "is_uc",
        "is_dla",
        "is_nonclient",
        "is_nts",
    ]
].reset_index(drop=True)

# ---------- CLEAN COMBOS FOR PIVOT (ignore Dormant in combo names) ----------
def clean_combo(combo_str):
    if not combo_str or combo_str == "(No Remark)":
        return "(No Remark)"
    parts = [p.strip() for p in combo_str.split("+")]
    cleaned = [p for p in parts if "dormant" not in p.lower()]
    return " + ".join(sorted(cleaned)) if cleaned else "Dormant Only"

exploded["RemarkCombo_Clean"] = exploded["RemarkCombo"].apply(clean_combo)

# ---------- BUILD PIVOT ----------
pivot = (
    exploded.pivot_table(
        index="Category",
        columns="RemarkCombo_Clean",
        values="Account",
        aggfunc=lambda x: x.nunique(),
        fill_value=0,
    )
)

pivot["Total"] = pivot.sum(axis=1)

# ---------- SUMMARY ----------
total_unique_accounts = int(agg["Account"].nunique())
total_reasons = int(pivot["Total"].sum())

print(f"Total unique accounts (all): {total_unique_accounts}")
print(f"Total reasons (grand total pivot - included accounts): {total_reasons}")
print(f"Dormant-only excluded: {dormant_count}")
print(f"UC excluded: {uc_count}")
print(f"DLA excluded: {dla_count}")
print(f"Non-client excluded: {nonclient_count}")
print(f"NTS accounts included: {nts_count}")

# ---------- EXCEL WRITER ----------
out_filename = "remark_combinations_output_final.xlsx"


def autofit_columns(writer, df, sheet_name):
    worksheet = writer.sheets[sheet_name]
    for idx, col in enumerate(df.columns):
        try:
            series = df[col].astype(str)
            max_len = max(series.map(len).max(), len(str(col)))
        except Exception:
            max_len = len(str(col))
        worksheet.set_column(idx, idx, max_len + 2)


with pd.ExcelWriter(out_filename, engine="xlsxwriter") as writer:
    # Pivot Overview
    pivot.to_excel(writer, sheet_name="Pivot_Overview", startrow=0)
    worksheet = writer.sheets["Pivot_Overview"]
    worksheet.freeze_panes(1, 0)

    # Write summary below
    nrows_pivot = pivot.shape[0] + 1
    insert_row = nrows_pivot + 2
    worksheet.write(insert_row, 0, "Total unique accounts:")
    worksheet.write(insert_row, 1, total_unique_accounts)
    worksheet.write(insert_row + 1, 0, "Total reasons (grand total of pivot):")
    worksheet.write(insert_row + 1, 1, total_reasons)
    worksheet.write(insert_row + 3, 0, "Dormant-only excluded:")
    worksheet.write(insert_row + 3, 1, dormant_count)
    worksheet.write(insert_row + 4, 0, "UC excluded:")
    worksheet.write(insert_row + 4, 1, uc_count)
    worksheet.write(insert_row + 5, 0, "DLA excluded:")
    worksheet.write(insert_row + 5, 1, dla_count)
    worksheet.write(insert_row + 6, 0, "Non-client excluded:")
    worksheet.write(insert_row + 6, 1, nonclient_count)
    worksheet.write(insert_row + 7, 0, "NTS accounts included:")
    worksheet.write(insert_row + 7, 1, nts_count)
    autofit_columns(writer, pivot.reset_index(), "Pivot_Overview")

    # Account_Aggregated
    agg.to_excel(writer, sheet_name="Account_Aggregated", index=False)
    autofit_columns(writer, agg, "Account_Aggregated")
    writer.sheets["Account_Aggregated"].freeze_panes(1, 0)

    # Account_Category
    exploded.to_excel(writer, sheet_name="Account_Category", index=False)
    autofit_columns(writer, exploded, "Account_Category")
    writer.sheets["Account_Category"].freeze_panes(1, 0)

    # Combo Sheets (original combos, not cleaned)
    combo_map = []
    combo_list_included = agg_cat["RemarkCombo"].dropna().unique().tolist()
    for i, combo in enumerate(combo_list_included, start=1):
        sheet_name = f"Combo_{i}"
        subset = exploded[(exploded["RemarkCombo"] == combo)].copy()
        subset.to_excel(writer, sheet_name=sheet_name, index=False)
        autofit_columns(writer, subset, sheet_name)
        writer.sheets[sheet_name].freeze_panes(1, 0)

        unique_all = agg.loc[agg["RemarkCombo"] == combo, "Account"].nunique()
        unique_included = agg_cat.loc[agg_cat["RemarkCombo"] == combo, "Account"].nunique()
        unique_excluded = agg.loc[mask_exclude & (agg["RemarkCombo"] == combo), "Account"].nunique()
        nts_in_combo = agg_cat.loc[
            (agg_cat["RemarkCombo"] == combo) & agg_cat["is_nts"], "Account"
        ].nunique()

        combo_map.append(
            {
                "Combo_Sheet": sheet_name,
                "RemarkCombo": str(combo),
                "Unique_Accounts_All": int(unique_all),
                "Unique_Accounts_IncludedForCategorization": int(unique_included),
                "Unique_Accounts_Excluded": int(unique_excluded),
                "NTS_Accounts_in_Combo": int(nts_in_combo),
            }
        )

    combo_df = pd.DataFrame(combo_map)
    combo_df.to_excel(writer, sheet_name="Combo_Index", index=False)
    autofit_columns(writer, combo_df, "Combo_Index")
    writer.sheets["Combo_Index"].freeze_panes(1, 0)

    # Excluded Sheets
    excluded_all = agg.loc[mask_exclude].copy()
    excluded_all.to_excel(writer, sheet_name="Excluded_All", index=False)
    autofit_columns(writer, excluded_all, "Excluded_All")
    writer.sheets["Excluded_All"].freeze_panes(1, 0)

    for col_flag, name in [
        ("is_dormant", "Excluded_DormantOnly"),
        ("is_uc", "Excluded_UC"),
        ("is_dla", "Excluded_DLA"),
        ("is_nonclient", "Excluded_NonClient"),
    ]:
        sub = agg.loc[agg[col_flag]].copy()
        sub.to_excel(writer, sheet_name=name, index=False)
        autofit_columns(writer, sub, name)
        writer.sheets[name].freeze_panes(1, 0)

print(f"\n✅ Saved file: {out_filename}")