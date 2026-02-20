def link_surnames(person_names):
    """
    Links standalone surnames to full names.
    Example:
      ['Katie Puris', 'John Matthews', 'Puris', 'Matthews']
      → ['Katie Puris', 'John Matthews']
    """

    full_names = []
    surname_map = {}

    # Pass 1: collect full names
    for name in person_names:
        parts = name.split()
        if len(parts) >= 2:
            full_names.append(name)
            surname_map[parts[-1]] = name  # last name → full name

    # Pass 2: resolve names
    resolved = []
    for name in person_names:
        parts = name.split()
        if len(parts) == 1 and name in surname_map:
            resolved.append(surname_map[name])
        else:
            resolved.append(name)

    # Deduplicate while preserving order
    return list(dict.fromkeys(resolved))
    

import string

def anonymise_news_article(article: str):
    ner_results = ner_pipeline(article)

    # Step 1: raw person spans
    person_names = extract_person_spans(article, ner_results)

    # Step 2: surname linking (KEY FIX)
    person_names = link_surnames(person_names)

    # Step 3: build PERSON_A, PERSON_B mapping
    alphabet = string.ascii_uppercase
    reverse_map = {}
    anonymised = article

    for i, name in enumerate(person_names):
        token = f"PERSON_{alphabet[i]}"
        reverse_map[token] = [name]
        anonymised = anonymised.replace(name, token)

    return anonymised, reverse_map
    
    