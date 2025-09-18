import pandas as pd
from bertopic import BERTopic

# =======================
# Step 1: Load and filter data
# =======================
file_path = "your_file.xlsx"   # change to your file path
df = pd.read_excel(file_path)

# Keep only rows with remark = "Total Block" and non-null comments
df_block = df[df["remark"].str.contains("Total Block", case=False, na=False)].copy()
df_block = df_block[df_block["note_block_sp_status"].notna()].copy()

# Clean repetitive phrases like "total block"
remove_phrases = ["total block", "blocked account", "account blocked"]

def clean_text(text):
    text = str(text).lower()
    for phrase in remove_phrases:
        text = text.replace(phrase, "")
    return text.strip()

df_block["clean_text"] = df_block["note_block_sp_status"].apply(clean_text)

# =======================
# Step 2: Run BERTopic
# =======================
topic_model = BERTopic(verbose=True)
topics, probs = topic_model.fit_transform(df_block["clean_text"].tolist())

df_block["topic"] = topics

# =======================
# Step 3: Explore topics
# =======================
# Print discovered topics with top keywords
print("\n=== Topics Discovered ===")
print(topic_model.get_topic_info())

# Show top keywords per topic
for t in set(topics):
    if t != -1:  # -1 is "outlier" cluster
        print(f"\nTopic {t}:")
        print(topic_model.get_topic(t))

# =======================
# Step 4: Save results
# =======================
df_block.to_excel("bertopic_total_block.xlsx", index=False)

# Optional: Visualize topics (requires notebook or interactive window)
# topic_model.visualize_topics().show()
# topic_model.visualize_barchart(top_n_topics=10).show()