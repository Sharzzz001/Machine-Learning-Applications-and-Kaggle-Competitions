import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import numpy as np

# =======================
# Step 1: Load and filter data
# =======================
file_path = "your_file.xlsx"   # change to your file path
df = pd.read_excel(file_path)

# Keep only rows with remark = "Total Block"
df_block = df[df["remark"].str.contains("Total Block", case=False, na=False)]
texts = df_block["note_block_sp_status"].dropna().astype(str).tolist()

# =======================
# Step 2: TF-IDF Vectorization
# =======================
vectorizer = TfidfVectorizer(stop_words="english", max_features=2000)
X = vectorizer.fit_transform(texts)

# =======================
# Step 3: Elbow method to find optimal k
# =======================
inertia = []
K_range = range(2, 11)  # test clusters from 2 to 10
for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(X)
    inertia.append(kmeans.inertia_)

plt.plot(K_range, inertia, marker='o')
plt.xlabel("Number of clusters (k)")
plt.ylabel("Inertia (Within-cluster sum of squares)")
plt.title("Elbow Method for Optimal k")
plt.show()

# =======================
# Step 4: Run KMeans with chosen k
# =======================
best_k = 5  # <-- after checking elbow curve, set this manually
kmeans = KMeans(n_clusters=best_k, random_state=42)
clusters = kmeans.fit_predict(X)

df_block["theme_cluster"] = clusters

# =======================
# Step 5: Show top keywords per cluster
# =======================
terms = vectorizer.get_feature_names_out()

def print_top_keywords_per_cluster(n_terms=10):
    for i in range(best_k):
        cluster_terms = np.argsort(kmeans.cluster_centers_[i])[-n_terms:]
        keywords = [terms[j] for j in cluster_terms]
        print(f"\nCluster {i}: {', '.join(keywords)}")

print_top_keywords_per_cluster()

# =======================
# Step 6: Show sample comments per cluster
# =======================
for i in range(best_k):
    samples = df_block[df_block["theme_cluster"] == i]["note_block_sp_status"].head(5).tolist()
    print(f"\n--- Cluster {i} Sample Comments ---")
    for s in samples:
        print("-", s)

# Save results if needed
df_block.to_excel("clustered_total_block.xlsx", index=False)