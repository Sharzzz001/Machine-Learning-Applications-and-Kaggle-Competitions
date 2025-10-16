import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import re
import os
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

categories = {
    "Overdue RR": ["overdue rr"],
    "IRPQ Attestation": ["irpq attestation", "irpa"],
    "Doc deficiency": ["doc deficiency"],
    "Court Hearing": ["court", "legal"],
    "FCC/CAC": ["cac"],
    "Sanction": ["sanction"],
    "Deceased": ["deceased", "death", "demise"],
    "Address Proof": ["address proof"],
    "Expired document": ["expired document"],
    "Initial funding": ["initial funding"],
}

category_labels = list(categories.keys())
category_embeddings = model.encode(category_labels, convert_to_tensor=True)

def categorize_notes(note, is_nts=False):
    if is_nts:
        return ["NTS"]
    if pd.isna(note) or str(note).strip() == "":
        return ["Blank"]
    note_text = str(note).lower()
    for cat, kws in categories.items():
        for kw in kws:
            if kw in note_text:
                return [cat]
    embedding = model.encode([note_text], convert_to_tensor=True)
    scores = util.cos_sim(embedding, category_embeddings)[0]
    best_idx = int(scores.argmax())
    best_cat = category_labels[best_idx]
    return [best_cat]

def process_files(active_file, dla_file, nts_file, out_file="remark_semantic_output.xlsx"):
    nts_df = pd.read_excel(nts_file)
    nts_df["Account Number"] = nts_df["Account Number"].astype(str)
    active_df = pd.read_excel(active_file)
    dla_df = pd.read_excel(dla_file, sheet_name="Sheet1")
    dla_df["Account Number"] = dla_df["Account Number"].astype(str)
    active_df = active_df[active_df["Number"].notna()]
    active_df["Remark"] = active_df["Remark"].fillna("")
    active_df = active_df.dropna(subset=["Number"]).copy()
    df = active_df.copy()
    if "Number" in df.columns and "Account" not in df.columns:
        df.rename(columns={"Number": "Account"}, inplace=True)
    df["Account"] = df["Account"].astype(str)
    note_cols = [c for c in df.columns if "note" in c.lower()]
    note_col = note_cols[0] if note_cols else "Note Block BP Status"
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
    nts_accounts = nts_df["Account Number"].unique()
    dla_accounts = dla_df["Account Number"].unique()
    df["is_nts"] = df["Account"].isin(nts_accounts)
    df["is_dla"] = df["Account"].isin(dla_accounts)
    agg = (
        df.groupby("Account", sort=False)
        .agg({"Remark": lambda x: sorted(set(x.dropna().astype(str))), note_col: lambda s: " || ".join(s.dropna().astype(str))})
        .reset_index()
        .rename(columns={note_col: "Notes"})
    )
    agg["Categories"] = agg.apply(lambda r: categorize_notes(r["Notes"], r["is_nts"]), axis=1)
    exploded = agg.explode("Categories").dropna(subset=["Categories"]).rename(
        columns={"Categories": "Category"}
    )
    pivot = (
        exploded.pivot_table(
            index="Category",
            columns="Remark",
            values="Account",
            aggfunc=lambda x: x.nunique(),
            fill_value=0,
        )
    )
    pivot["Total"] = pivot.sum(axis=1)
    with pd.ExcelWriter(out_file, engine="xlsxwriter") as writer:
        pivot.to_excel(writer, sheet_name="Pivot_Overview")
        agg.to_excel(writer, sheet_name="Account_Aggregated", index=False)
        exploded.to_excel(writer, sheet_name="Account_Category", index=False)
    return out_file

def run_gui():
    root = tk.Tk()
    root.title("Semantic Categorisation EUC")
    inputs = {"active": tk.StringVar(), "dla": tk.StringVar(), "nts": tk.StringVar()}
    def choose_file(key):
        filename = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if filename:
            inputs[key].set(filename)
    def run_process():
        active_file = inputs["active"].get()
        dla_file = inputs["dla"].get()
        nts_file = inputs["nts"].get()
        if not (active_file and dla_file and nts_file):
            messagebox.showwarning("Missing", "Please select all 3 files")
            return
        out_file = process_files(active_file, dla_file, nts_file)
        if out_file:
            messagebox.showinfo("Done", f"Report saved:\n{out_file}")
            root.destroy()
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