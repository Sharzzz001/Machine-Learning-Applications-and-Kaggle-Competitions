df_block["clean_text"] = df_block["note_block_sp_status"].str.replace(
    r"\btotal block\b", "", case=False, regex=True
)