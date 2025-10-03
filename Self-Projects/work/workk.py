from sentence_transformers import SentenceTransformer, util
import pandas as pd

# -----------------
# 1. Load MiniLM
# -----------------
model = SentenceTransformer("all-MiniLM-L6-v2")  # use local path if downloaded

# -----------------
# 2. Define Keyword Map (your existing categories)
# -----------------
keyword_map = {
    "Overdue RR": ["overdue rr", "rolling review overdue", "rr overdue"],
    "Doc Pending": ["pending documents", "docs missing", "document pending"],
    "Screening": ["name screening", "screen check", "screening in progress"],
    # add all your existing categories here...
}

# Flatten keywords and keep category
keyword_df = pd.DataFrame([
    {"category": cat, "keyword": kw}
    for cat, kws in keyword_map.items()
    for kw in kws
])

# Precompute embeddings for keywords
keyword_embeddings = model.encode(keyword_df["keyword"].tolist(), convert_to_tensor=True)

# -----------------
# 3. Semantic Mapper
# -----------------
def map_text_to_category(text, threshold=0.6):
    """Map free-flow text to nearest category using MiniLM similarity."""
    if pd.isna(text) or not str(text).strip():
        return "Uncategorized"
    
    text_emb = model.encode(str(text), convert_to_tensor=True)
    cos_sim = util.cos_sim(text_emb, keyword_embeddings)[0]
    best_idx = int(cos_sim.argmax())
    best_score = float(cos_sim[best_idx])
    
    if best_score >= threshold:
        return keyword_df.iloc[best_idx]["category"]
    return "Uncategorized"

# -----------------
# 4. Apply to your dataframe
# -----------------
# Example: earlier you had agg["RemarkCombo"] or agg["Notes"]
agg["Category"] = agg["Notes"].apply(map_text_to_category)

# -----------------
# 5. Continue with your pivot pipeline
# -----------------
exploded = agg.explode("Category").copy()
exploded = exploded.dropna(subset=["Category"])
exploded = exploded.rename(columns={"Category": "Category"})
exploded = exploded[["Account", "RemarkCombo", "Category", "Notes"]].reset_index(drop=True)

pivot = exploded.pivot_table(
    index="Category",
    columns="RemarkCombo",
    values="Account",
    aggfunc=lambda x: x.nunique(),
    fill_value=0
)