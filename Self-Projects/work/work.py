import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load a pre-trained BERT model for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

# Example DataFrames
df1 = pd.DataFrame({'Error description': [
    "Trade failed due to missing field",
    "Invalid date format in trade",
    "Collateral amount not provided"
]})

df2 = pd.DataFrame({'JIRA ID': ['JIRA-101', 'JIRA-102', 'JIRA-103'],
                    'JIRA description': [
    "Trade failed due to missing field. User tried to re-input.",
    "Wrong date format. System rejected the trade.",
    "Collateral value missing — failed at validation."
]})

# Embed the error descriptions and JIRA descriptions using BERT
error_embeddings = model.encode(df1['Error description'].tolist(), convert_to_tensor=True)
jira_embeddings = model.encode(df2['JIRA description'].tolist(), convert_to_tensor=True)

# Calculate cosine similarity
similarity_matrix = cosine_similarity(error_embeddings.cpu().numpy(), jira_embeddings.cpu().numpy())

# Match each error with the most similar JIRA description
matches = []

for i, error_desc in enumerate(df1['Error description']):
    best_match_idx = similarity_matrix[i].argmax()
    best_match_score = similarity_matrix[i][best_match_idx]

    matches.append({
        'Error description': error_desc,
        'Closest JIRA': df2['JIRA description'].iloc[best_match_idx],
        'JIRA ID': df2['JIRA ID'].iloc[best_match_idx],
        'Similarity Score': best_match_score
    })

# Create a DataFrame with the results
mapped_df = pd.DataFrame(matches)
print(mapped_df)