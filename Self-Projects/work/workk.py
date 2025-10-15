import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import re
import os

# ---------- Your processing function ----------
def process_files(active_file, dla_file, nts_file, out_file="remark_combinations_output.xlsx"):
    try:
        # ---------- READ INPUT FILES ----------
        nts_df = pd.read_excel(nts_file)
        nts_df["Account Number"] = nts_df["Account Number"].astype(str)

        active_df = pd.read_excel(active_file)
        dla_df = pd.read_excel(dla_file, sheet_name="Sheet1")
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

        # find notes column
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

        # ---------- KEYWORD MAP ----------
        keyword_map = {
            "Overdue RR": ["overdue rr"],
            "IRPQ Attestation": ["irpq attestation", "irpa"],
            "Doc deficiency": ["doc deficiency"],
            "Court Hearing": ["court", "legal"],
            "FCC/CAC": ["cac"],
            "Sanction": ["sanction"],
            "Deceased": ["deceased", "death", "demise"],
        }

        def categories_for_account(row):
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
            return list(dict.fromkeys(matches))

        agg_cat["Categories"] = agg_cat.apply(categories_for_account, axis=1)

        # ---------- EXPLODE ----------
        exploded = agg_cat.explode("Categories").dropna(subset=["Categories"]).rename(
            columns={"Categories": "Category"}
        )
        exploded = exploded.reset_index(drop=True)

        # ---------- CLEAN COMBOS FOR PIVOT ----------
        def clean_combo(combo_str):
            if not combo_str or combo_str == "(No Remark)":
                return "(No Remark)"
            parts = [p.strip() for p in combo_str.split("+")]
            cleaned = [p for p in parts if "dormant" not in p.lower()]
            return " + ".join(sorted(cleaned)) if cleaned else "Dormant Only"

        exploded["RemarkCombo_Clean"] = exploded["RemarkCombo"].apply(clean_combo)

        # ---------- PIVOT ----------
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

        # ---------- REPORT STYLE ----------
        remark_combo_totals = (
            exploded.groupby("RemarkCombo_Clean")["Account"]
            .nunique()
            .reindex(pivot.columns.drop("Total"), fill_value=0)
        )
        remark_combo_totals["Total"] = remark_combo_totals.sum()

        rows = []
        rows.append(["Total Volume (Unique Accounts)"] + remark_combo_totals.tolist())
        rows.append(["Block Reasons"] + [""] * len(remark_combo_totals))
        for cat, row in pivot.iterrows():
            rows.append([cat] + row.tolist())

        report_pivot = pd.DataFrame(
            rows, columns=["Block Code"] + remark_combo_totals.index.tolist()
        )

        # ---------- WRITE TO EXCEL ----------
        with pd.ExcelWriter(out_file, engine="xlsxwriter") as writer:
            report_pivot.to_excel(writer, sheet_name="Pivot_Overview", index=False)

        return out_file

    except Exception as e:
        messagebox.showerror("Error", str(e))
        return None


# ---------- Tkinter GUI ----------
def run_gui():
    root = tk.Tk()
    root.title("Account Blocks EUC")

    inputs = {"active": tk.StringVar(), "dla": tk.StringVar(), "nts": tk.StringVar()}

    def choose_file(key):
        filename = filedialog.askopenfilename(
            title=f"Select {key.upper()} Excel file",
            filetypes=[("Excel files", "*.xlsx *.xls")],
        )
        if filename:
            inputs[key].set(filename)

    def run_process():
        active_file = inputs["active"].get()
        dla_file = inputs["dla"].get()
        nts_file = inputs["nts"].get()
        if not (active_file and dla_file and nts_file):
            messagebox.showwarning("Missing file", "Please select all 3 input files")
            return
        out_file = process_files(active_file, dla_file, nts_file)
        if out_file:
            messagebox.showinfo("Done", f"Report saved as:\n{out_file}")

    # Layout
    tk.Label(root, text="Active Accounts File:").grid(row=0, column=0, sticky="w")
    tk.Entry(root, textvariable=inputs["active"], width=50).grid(row=0, column=1)
    tk.Button(root, text="Browse", command=lambda: choose_file("active")).grid(row=0, column=2)

    tk.Label(root, text="DLA File:").grid(row=1, column=0, sticky="w")
    tk.Entry(root, textvariable=inputs["dla"], width=50).grid(row=1, column=1)
    tk.Button(root, text="Browse", command=lambda: choose_file("dla")).grid(row=1, column=2)

    tk.Label(root, text="NTS File:").grid(row=2, column=0, sticky="w")
    tk.Entry(root, textvariable=inputs["nts"], width=50).grid(row=2, column=1)
    tk.Button(root, text="Browse", command=lambda: choose_file("nts")).grid(row=2, column=2)

    tk.Button(root, text="Run", command=run_process, bg="green", fg="white").grid(
        row=3, column=0, columnspan=3, pady=10
    )

    root.mainloop()


if __name__ == "__main__":
    run_gui()