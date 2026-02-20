def extract_person_spans(text, ner_results):
    """
    Groups contiguous PERSON tokens into full name spans.
    Returns list of unique person strings.
    """
    persons = []
    current_tokens = []
    current_end = None

    for ent in ner_results:
        if ent["entity"].startswith("B-PER") or ent["entity"].startswith("I-PER"):
            start = ent["start"]
            end = ent["end"]

            if current_end is None or start == current_end:
                current_tokens.append(text[start:end])
                current_end = end
            else:
                persons.append("".join(current_tokens))
                current_tokens = [text[start:end]]
                current_end = end
        else:
            if current_tokens:
                persons.append("".join(current_tokens))
                current_tokens = []
                current_end = None

    if current_tokens:
        persons.append("".join(current_tokens))

    # Deduplicate while preserving order
    return list(dict.fromkeys(persons))
    

import string

def anonymise_news_article(article: str):
    ner_results = ner_pipeline(article)

    # Step 1: extract person names
    person_names = extract_person_spans(article, ner_results)

    # Step 2: build mapping
    alphabet = string.ascii_uppercase
    person_map = {}
    reverse_map = {}

    for i, name in enumerate(person_names):
        token = f"PERSON_{alphabet[i]}"
        person_map[name] = token
        reverse_map[token] = [name]

    # Step 3: replace names (longest first)
    anonymised = article
    for name in sorted(person_map, key=len, reverse=True):
        anonymised = anonymised.replace(name, person_map[name])

    return anonymised, reverse_map
    
article = """
Katie Puris said she would respond to the allegations.
John Matthews criticised the statement.
Puris later clarified her position, Matthews responded again.
"""

anon_text, mapping = anonymise_news_article(article)

print(anon_text)
print(mapping)