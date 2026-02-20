from fastcoref import FCoref
import string

# Initialise coreference model (CPU is fine)
coref = FCoref(device="cpu")


def anonymise_persons_in_article(article: str) -> str:
    """
    Replaces all person mentions in a news article with PERSON_A, PERSON_B, etc.
    Uses coreference resolution to ensure consistency.
    """

    preds = coref.predict(texts=[article])
    clusters = preds[0].get_clusters(as_strings=True)

    anonymised = article
    alphabet = string.ascii_uppercase

    for i, cluster in enumerate(clusters):
        person_token = f"PERSON_{alphabet[i]}"

        # Replace longer mentions first to avoid partial overlaps
        for mention in sorted(cluster, key=len, reverse=True):
            anonymised = anonymised.replace(mention, person_token)

    return anonymised
    
    
article = """
Katie Puris said she would respond to the allegations.
After Puris’ initial claim, she clarified her position.

John Matthews criticised the statement. Matthews said he disagreed with Puris.
"""

print(anonymise_persons_in_article(article))

