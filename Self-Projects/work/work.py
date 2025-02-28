from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Convert descriptions to vectors
vectorizer = TfidfVectorizer()
error_vectors = vectorizer.fit_transform(df1['Error description'])
jira_vectors = vectorizer.transform(df2['JIRA description'])

# Calculate similarity scores
similarity_matrix = cosine_similarity(error_vectors, jira_vectors)

# Map errors to the most similar JIRA description
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