remove_phrases = ["total block", "blocked account", "account blocked"]

def clean_text(text):
    text = text.lower()
    for phrase in remove_phrases:
        text = text.replace(phrase, "")
    return text.strip()

df_block["clean_text"] = df_block["note_block_sp_status"].astype(str).apply(clean_text)