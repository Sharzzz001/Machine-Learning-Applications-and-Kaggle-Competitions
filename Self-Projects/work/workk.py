from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine
import numpy as np

# Load MiniLM model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Example list of “keywords” you want to match to categories
keyword_map = {
    "Overdue": ["overdue rr", "regulatory review overdue", "rr overdue"],
    "Expired Doc": ["expired document", "document expired", "expiry"],
    "KYC Issue": ["kyc not verified", "kyc missing", "kyc expired"],
}

# Precompute embeddings for all keyword phrases
keyword_embeddings = {}
for cat, phrases in keyword_map.items():
    # You may choose to average phrase embeddings for a category
    emb_list = model.encode(phrases)
    # average the embeddings
    keyword_embeddings[cat] = np.mean(emb_list, axis=0)

def find_best_category(note_text, threshold=0.6):
    """
    Given a free-flow note text, compute its embedding,
    compare with each category embedding by cosine similarity,
    and pick the best category if above threshold.
    """
    if not note_text or str(note_text).strip() == "":
        return None

    emb = model.encode([note_text])[0]

    best_cat = None
    best_score = -1
    for cat, cat_emb in keyword_embeddings.items():
        # cosine similarity = 1 - cosine distance
        sim = 1 - cosine(emb, cat_emb)
        if sim > best_score:
            best_score = sim
            best_cat = cat

    if best_score >= threshold:
        return best_cat, best_score
    else:
        return None

# Example usage
notes = [
    "client has rr overdue and pending",
    "document has expired since last month",
    "kyc docs are missing",
    "something entirely unrelated"
]

for note in notes:
    result = find_best_category(note, threshold=0.5)
    print(f"Note: {note!r} -> Match: {result}")