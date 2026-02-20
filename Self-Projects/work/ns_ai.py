from transformers import pipeline

ner_pipeline = pipeline(
    task="ner",
    model=model,
    tokenizer=tokenizer
)

def extract_person_spans(text, ner_results):
    """
    Robustly groups B-PER / I-PER tokens into full person names.
    Works with modern Transformers outputs.
    """

    # Sort entities by character offset (CRITICAL)
    ner_results = sorted(ner_results, key=lambda x: x["start"])

    persons = []
    current_start = None
    current_end = None

    for ent in ner_results:
        label = ent["entity"]
        start = ent["start"]
        end = ent["end"]

        if label == "B-PER":
            # Close any existing entity
            if current_start is not None:
                persons.append(text[current_start:current_end])

            current_start = start
            current_end = end

        elif label == "I-PER" and current_start is not None:
            # Extend current entity
            current_end = end

        else:
            # Non-person token → close current entity
            if current_start is not None:
                persons.append(text[current_start:current_end])
                current_start = None
                current_end = None

    # Catch final open entity
    if current_start is not None:
        persons.append(text[current_start:current_end])

    # Deduplicate while preserving order
    return list(dict.fromkeys(persons))
    
import string

def anonymise_news_article(article: str):
    ner_results = ner_pipeline(article)

    person_names = extract_person_spans(article, ner_results)

    alphabet = string.ascii_uppercase
    person_map = {}
    reverse_map = {}

    for i, name in enumerate(person_names):
        token = f"PERSON_{alphabet[i]}"
        person_map[name] = token
        reverse_map[token] = [name]

    anonymised = article
    for name in sorted(person_map, key=len, reverse=True):
        anonymised = anonymised.replace(name, person_map[name])

    return anonymised, reverse_map
    
    
    