import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from transformers import AutoTokenizer, AutoModelForTokenClassification

MODEL_PATH = "/secure/models/ner-model"

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

model = AutoModelForTokenClassification.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

ner_pipeline = pipeline(
    "ner",
    model=model,
    tokenizer=tokenizer,
    grouped_entities=True
)

def anonymise_news_article(article: str):
    """
    Takes a news article and returns:
    1. An anonymised article with PERSON_A, PERSON_B, ...
    2. A mapping of PERSON_X -> list of original mentions
    """

    ner_results = ner_pipeline(article)

    # Step 1: extract PERSON entities
    persons = []
    for ent in ner_results:
        if ent["entity_group"] in ("PER", "PERSON"):
            persons.append(ent["word"])

    # Deduplicate while preserving order
    unique_persons = list(dict.fromkeys(persons))

    # Step 2: build PERSON_A / PERSON_B mapping
    alphabet = string.ascii_uppercase
    person_map = {}
    reverse_map = {}

    for i, name in enumerate(unique_persons):
        token = f"PERSON_{alphabet[i]}"
        person_map[name] = token
        reverse_map.setdefault(token, []).append(name)

    # Step 3: replace names in article (longest first)
    anonymised_article = article
    for name in sorted(person_map.keys(), key=len, reverse=True):
        anonymised_article = anonymised_article.replace(
            name, person_map[name]
        )

    return anonymised_article, reverse_map
    
    
article = """
Katie Puris said she would respond to the allegations.
John Matthews criticised the statement.
Puris later clarified her position, Matthews responded again.
"""

anon_text, mapping = anonymise_news_article(article)

print("ANONYMISED ARTICLE:\n")
print(anon_text)

print("\nPERSON MAPPING:\n")
for k, v in mapping.items():
    print(f"{k}: {v}")