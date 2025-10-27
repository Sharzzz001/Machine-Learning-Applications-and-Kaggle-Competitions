# crs_runner.py
# -*- coding: utf-8 -*-

import os
import sys
import re
import glob
import time
import zipfile
import hashlib
import logging
import subprocess
from math import floor
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import numpy as np
import requests
from requests.auth import HTTPBasicAuth

# =========================
# CONFIG / CONSTANT PATHS
# =========================

PATHS = {
    # Working root for this job (no trailing slash)
    "PROJECT_ROOT": r"H:\python_projects\NEWS CRS Fetch Script",
    # Java location (Zulu JDK bin)
    "JAVA_BIN": r"C:\Program Files (x86)\Zulu\zulu-8\bin\java.exe",
    # AxialEOD bootstrapper JAR
    "BOOTSTRAP_JAR": r"H:\python_projects\NEWS CRS Fetch Script\axialeod-client-scripts-2.0.11\lib\axialeod-client-scripts-bootstrapper.jar",
    # Download destination (where the Java client will drop the zip)
    "DEST_DIR": r"H:\python_projects\NEWS CRS Fetch Script\Input CRS",
    # Output directory for per-account Excel files
    "OUTPUT_DIR": r"H:\python_projects\NEWS CRS Fetch Script\Output",
    # Temp extraction directory
    "EXTRACT_DIR": r"H:\python_projects\NEWS CRS Fetch Script\Extracted",
    # Nomura SSO helper directory (for token)
    "SSO_HELPER_DIR": r"C:\Program Files\Nomura\SSOHelper",
    # Nomura SSO helper exe
    "SSO_EXE": "TEACppClient.exe",
    # Upload endpoint
    "UPLOAD_URL": "http://axialeodpub.nomura.com/axialeod/upload",
}

# Feed codes (as per your note)
FEEDS = {
    "VD":  "CASHPBORS_GL_MULTI_T_SETT_ADH_EOD_XLS_SPR_CRS_PC_CASHFLOWS_VD_ZIP",
    "VD1": "CASHPBORS_GL_MULTI_T_SETT_ADH_EOD_XLS_SPR_CRS_PC_CASHFLOWS_VD1_ZIP",
}

# API upload metadata
UPLOAD_META = {
    "DEST_PATH": "/OTCSETTLE_PCF/TEST",
    # FEED_CODE is fixed per your OCR text
    "FEED_CODE": "OTCSETTLE_PC_IN_MULTI_ANL_CSHFLW_DW_EOD_OTHER_CRS_CALCULATIONS_COB_ZIP_1",
}

# Sheets we expect
SHEETS = [
    "Summary",
    "Cashflow",
    "Unwind Detail",
    "Dividend",
    "Reset",
    "Interest Reset Detail",
]

# Optional classification buckets used in validations (kept from your script)
RESET_TYPES = ['Fees Reset', 'Interest Reset', 'Spread Reset']
UNWIND_TYPES = ['Interest Partial Unwind', 'Fees Partial Unwind', 'Spread Partial Unwind']

# Pandas settings
pd.options.mode.chained_assignment = None


# =========================
# LOGGING
# =========================

def setup_logging():
    log_dir = Path(PATHS["PROJECT_ROOT"]) / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"crs_runner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(console)
    logging.info(f"Logging to {log_file}")


# =========================
# UTILITIES
# =========================

def ensure_dirs():
    for key in ("DEST_DIR", "OUTPUT_DIR", "EXTRACT_DIR"):
        Path(PATHS[key]).mkdir(parents=True, exist_ok=True)


def utc_now():
    return datetime.now(timezone.utc)


def pick_feed_by_gmt(now_utc: datetime) -> str:
    """
    Your requirement:
      - 06:30 GMT  -> FEEDS['VD']
      - 08:30 GMT  -> FEEDS['VD']
      - 09:30 GMT  -> FEEDS['VD1']
    This script is scheduled exactly at 06:30, 08:30, and 09:30 every day.
    We'll match exact HH:MM to be safe; otherwise default to VD.
    """
    hh = now_utc.hour
    mm = now_utc.minute
    if hh == 9 and mm == 30:
        return FEEDS["VD1"]
    if (hh in (6, 8)) and mm == 30:
        return FEEDS["VD"]
    # Fallback: VD
    return FEEDS["VD"]


def run_java_download(feed_code: str, the_date: datetime) -> subprocess.CompletedProcess:
    """
    Invokes the AxialEOD Java client with dynamic date (YYYYMMDD).
    """
    yyyymmdd = the_date.strftime("%Y%m%d")
    dest_dir = PATHS["DEST_DIR"]

    cmd = [
        PATHS["JAVA_BIN"], "-jar", PATHS["BOOTSTRAP_JAR"],
        feed_code, yyyymmdd, "LATEST",
        f"--environment=PROD",
        f'--destinationDir="{dest_dir}"'
    ]

    logging.info("Running Java download:")
    logging.info(" ".join(cmd))

    # We run from the project root to keep relative outputs sensible
    proc = subprocess.run(" ".join(cmd), shell=True, capture_output=True, text=True, cwd=PATHS["PROJECT_ROOT"])
    logging.info(f"Java stdout:\n{proc.stdout}")
    if proc.returncode != 0:
        logging.error(f"Java stderr:\n{proc.stderr}")
        raise RuntimeError(f"Java download failed with exit code {proc.returncode}")
    return proc


def latest_zip_in_dest() -> Path:
    """
    Pick the most recent .zip in DEST_DIR
    """
    zips = list(Path(PATHS["DEST_DIR"]).glob("*.zip"))
    if not zips:
        raise FileNotFoundError("No ZIP files found in destination directory after download.")
    zips.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return zips[0]


def extract_zip(zip_path: Path, extract_to: Path) -> list[Path]:
    """
    Extracts zip and returns list of extracted files
    """
    logging.info(f"Extracting: {zip_path} -> {extract_to}")
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)
        members = [extract_to / name for name in zf.namelist()]
    return members


def find_xlsx(extracted_files: list[Path]) -> Path:
    """
    Locate the primary XLSX to read. 
    We take the first .xlsx found (or the newest if multiple).
    """
    xlsxs = [p for p in extracted_files if p.suffix.lower() in (".xlsx", ".xls")]
    if not xlsxs:
        raise FileNotFoundError("No XLS/XLSX found inside the ZIP.")
    xlsxs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return xlsxs[0]


def parse_dates_inplace(df: pd.DataFrame):
    """
    Convert columns containing 'date' (case-insensitive) to datetime (coerce).
    """
    for col in df.columns:
        if "date" in col.lower():
            df[col] = pd.to_datetime(df[col], errors="coerce")


def load_all_sheets(xlsx_path: Path) -> dict[str, pd.DataFrame]:
    """
    Load required sheets if present; ignore missing with a warning.
    """
    logging.info(f"Loading workbook: {xlsx_path}")
    dfx = pd.read_excel(xlsx_path, sheet_name=None)
    out = {}
    for s in SHEETS:
        if s in dfx:
            df = dfx[s].copy()
            parse_dates_inplace(df)
            out[s] = df
        else:
            logging.warning(f"Sheet missing: {s}")
            out[s] = pd.DataFrame()
    return out


def split_and_save_per_account(sheets: dict[str, pd.DataFrame], out_dir: Path):
    """
    For each ACCOUNT_ID present in Summary, write an XLSX with all sheets filtered to that ACCOUNT_ID.
    """
    summary = sheets.get("Summary", pd.DataFrame())
    if summary.empty or "ACCOUNT_ID" not in summary.columns:
        raise ValueError("Summary sheet missing or lacks ACCOUNT_ID column.")

    account_ids = summary["ACCOUNT_ID"].dropna().astype(str).unique().tolist()
    logging.info(f"Found {len(account_ids)} accounts to write.")

    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for acc in account_ids:
        acc_safe = re.sub(r'[^\w.-]+', '_', acc)
        out_path = out_dir / f"{acc_safe}.xlsx"

        with pd.ExcelWriter(out_path, engine="xlsxwriter", datetime_format="d-MMM-yy") as writer:
            for sname, df in sheets.items():
                if df.empty:
                    # still create an empty tab to keep structure stable
                    pd.DataFrame().to_excel(writer, sheet_name=sname, index=False)
                    continue

                # Best-effort filter by known account columns
                cand_cols = [c for c in df.columns if c.strip().lower() in ("account_id", "accountid", "account id")]
                if cand_cols:
                    fdf = df[df[cand_cols[0]].astype(str) == acc]
                else:
                    # If no account column, just write whole sheet
                    fdf = df

                fdf.to_excel(writer, sheet_name=sname, index=False)

        count += 1

    logging.info(f"Wrote {count} per-account files to {out_dir}")
    return count


def zip_folder(folder_path: Path, zip_file_path: Path) -> int:
    """
    Zip all .xlsx and .csv files in folder_path. Return number of files zipped.
    """
    file_count = 0
    logging.info(f"Zipping files from {folder_path} -> {zip_file_path}")
    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith((".xlsx", ".csv")):
                    fp = Path(root) / file
                    zipf.write(fp, arcname=str(fp.relative_to(folder_path)))
                    file_count += 1
    logging.info(f"Zipped {file_count} files.")
    return file_count


def md5_of_file(file_path: Path) -> str:
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def write_md5_info(zip_path: Path, info_path: Path, date_str: str, file_count: int):
    md5sum = md5_of_file(zip_path)
    logging.info(f"MD5({zip_path.name}) = {md5sum}")
    with open(info_path, "w", encoding="utf-8") as f:
        f.write(f"filename: {zip_path.name}\n")
        f.write(f"md5: {md5sum}\n")
        f.write(f"date: {date_str}\n")
        f.write(f"file_count: {file_count}\n")
    logging.info(f"Wrote info file: {info_path}")


def get_nomura_token_and_user():
    """
    Launch SSO helper, parse token & user from its output.
    Assumes it prints lines containing 'Token: <...>' and 'Token: <user>|<...>' based on your OCR.
    We search conservatively for two captures.
    """
    exe_dir = PATHS["SSO_HELPER_DIR"]
    exe = PATHS["SSO_EXE"]

    logging.info("Retrieving Nomura token via SSO helper...")
    proc = subprocess.run(
        exe,
        shell=True,
        capture_output=True,
        text=True,
        cwd=exe_dir
    )
    out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    # Try robust regex patterns (using non-greedy)
    # Example OCR hints:
    #   Token: >...<   OR   "Token: <user>|<token>"
    token = None
    user = None

    m_user = re.search(r"Token:\s*([^\|\s<>]+)\|", out, flags=re.IGNORECASE)
    if m_user:
        user = m_user.group(1)

    m_token = re.search(r"Token:\s*<?([^<>\|\r\n]+)>?", out, flags=re.IGNORECASE)
    if m_token:
        token = m_token.group(1)
        # If a user|token line was matched as token, refine by taking the part after '|'
        if '|' in token:
            token = token.split('|', 1)[-1]

    if not token or not user:
        logging.debug(out)
        raise RuntimeError("Failed to parse Nomura token/user from SSO helper output.")

    logging.info(f"Parsed user={user}, token length={len(token)}")
    return user, token


def upload_zip_and_info(zip_path: Path, info_path: Path, eff_date_mmdd: str):
    user, token = get_nomura_token_and_user()

    files = {
        "DATA_FILE": open(zip_path, "rb"),
        "CKSUM_FILE": open(info_path, "rb"),
    }
    data = {
        "DEST_PATH": UPLOAD_META["DEST_PATH"],
        "EFF_DATE": eff_date_mmdd,
        "FEED_CODE": UPLOAD_META["FEED_CODE"],
    }

    logging.info(f"Uploading to {PATHS['UPLOAD_URL']} ...")
    try:
        r = requests.post(
            PATHS["UPLOAD_URL"],
            auth=HTTPBasicAuth(username=user, password=token),
            files=files,
            data=data,
            timeout=120
        )
    finally:
        files["DATA_FILE"].close()
        files["CKSUM_FILE"].close()

    if r.status_code == 200:
        logging.info(f"Upload Successful: {r.text}")
    else:
        logging.error(f"Upload Failed: {r.status_code} {r.text}")
        raise RuntimeError(f"Upload failed with status {r.status_code}")


# =========================
# MAIN LOGIC
# =========================

def main():
    setup_logging()
    ensure_dirs()

    now_utc = utc_now()
    logging.info(f"Current GMT time: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    feed_code = pick_feed_by_gmt(now_utc)
    logging.info(f"Selected feed: {feed_code}")

    # 1) Download
    run_java_download(feed_code, the_date=now_utc)

    # 2) Find latest zip & extract
    latest_zip = latest_zip_in_dest()
    extracted_files = extract_zip(latest_zip, Path(PATHS["EXTRACT_DIR"]))
    xlsx_path = find_xlsx(extracted_files)

    # 3) Load sheets
    sheets = load_all_sheets(xlsx_path)

    # (Optional) Example of a small validation similar to your original logic:
    # Attempt to reformat VALUE_DATE in Summary if present
    if "Summary" in sheets and not sheets["Summary"].empty and "VALUE_DATE" in sheets["Summary"].columns:
        s = sheets["Summary"]
        # Force datetime and then to %d-%b-%y uppercase
        s["VALUE_DATE"] = pd.to_datetime(s["VALUE_DATE"], errors="coerce")
        s["VALUE_DATE_FMT"] = s["VALUE_DATE"].dt.strftime("%d-%b-%y").str.upper()

    # 4) Split per account & save multi-sheet Excel files
    out_dir = Path(PATHS["OUTPUT_DIR"])
    # Clear previous outputs (optional; comment out if not desired)
    # for f in out_dir.glob("*.xlsx"):
    #     f.unlink(missing_ok=True)

    split_count = split_and_save_per_account(sheets, out_dir)

    # 5) Create zip + md5 info
    stamp_ymd = now_utc.strftime("%Y%m%d")
    stamp_mmdd = now_utc.strftime("%m%d")

    zip_out = Path(PATHS["DEST_DIR"]) / f"CRS_Calculations_CoB_{stamp_ymd}.zip"
    info_out = Path(PATHS["DEST_DIR"]) / f"CRS_Calculations_CoB_{stamp_ymd}.zip.info"

    files_zipped = zip_folder(out_dir, zip_out)
    write_md5_info(zip_out, info_out, date_str=stamp_mmdd, file_count=files_zipped)

    # 6) Upload
    upload_zip_and_info(zip_out, info_out, eff_date_mmdd=stamp_mmdd)

    logging.info("All done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception(f"Fatal error: {e}")
        # Non-zero exit helps Task Scheduler treat it as a failure
        sys.exit(1)