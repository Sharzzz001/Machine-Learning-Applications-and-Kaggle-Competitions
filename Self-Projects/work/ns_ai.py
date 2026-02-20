def extract_person_spans(text, ner_results):
    """
    Groups contiguous B-PER / I-PER tokens into full person names.
    Returns list of unique person names in appearance order.
    """
    persons = []
    current_start = None
    current_end = None

    for ent in ner_results:
        label = ent["entity"]
        start = ent["start"]
        end = ent["end"]

        if label == "B-PER":
            # Close previous entity
            if current_start is not None:
                persons.append(text[current_start:current_end])

            # Start new entity
            current_start = start
            current_end = end

        elif label == "I-PER" and current_start is not None:
            # Extend current entity
            current_end = end

        else:
            # Non-PER token → close entity if open
            if current_start is not None:
                persons.append(text[current_start:current_end])
                current_start = None
                current_end = None

    # Catch last open entity
    if current_start is not None:
        persons.append(text[current_start:current_end])

    # Deduplicate while preserving order
    return list(dict.fromkeys(persons))
    
    
import string

def anonymise_news_article(article: str):
    ner_results = ner_pipeline(article)

    # Correctly grouped full names
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
    
