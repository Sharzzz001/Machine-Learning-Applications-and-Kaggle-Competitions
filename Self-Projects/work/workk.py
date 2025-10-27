import subprocess, re, logging
from pathlib import Path

def run_sso_helper_and_extract():
    exe_path = Path(PATHS["SSO_HELPER_DIR"]) / "TeaCppClient.exe"
    if not exe_path.is_file():
        raise FileNotFoundError(f"Cannot find {exe_path}")

    # run with 'ldap' arg, capture text directly
    proc = subprocess.run(
        [str(exe_path), "ldap"],
        cwd=PATHS["SSO_HELPER_DIR"],
        capture_output=True,
        text=True,      # auto-decodes stdout/stderr
        shell=False
    )

    if proc.returncode != 0:
        raise RuntimeError(f"SSO helper failed rc={proc.returncode}, stderr={proc.stderr}")

    out = proc.stdout + proc.stderr
    logging.debug(f"SSO raw output:\n{out}")

    # regexes (you’ll tune once you see actual output)
    match_token = re.search(r"Token:\s*<?([^<>\|\r\n]+)>?", out, re.IGNORECASE)
    match_user  = re.search(r"Token:\s*([^\|\s<>]+)\|", out, re.IGNORECASE)

    mytoken = match_token.group(1).strip() if match_token else None
    myuser  = match_user.group(1).strip() if match_user else None

    return myuser, mytoken