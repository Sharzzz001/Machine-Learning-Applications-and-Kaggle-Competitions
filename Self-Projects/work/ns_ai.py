import re

def safe_replace(text, phrase, replacement):
    """
    Replaces whole-word phrases safely, including possessives.
    """
    escaped = re.escape(phrase)

    # Match:
    # - whole word
    # - optional possessive ('s or ’s)
    pattern = rf"\b{escaped}\b(?:['’]s)?"

    return re.sub(pattern, replacement, text)
    
def build_person_aliases(person_names):
    """
    Returns:
    {
      "PERSON_A": ["Katie Puris", "Puris"],
      "PERSON_B": ["John Matthews", "Matthews"]
    }
    """
    full_names = []
    surname_map = {}

    for name in person_names:
        parts = name.split()
        if len(parts) >= 2:
            full_names.append(name)
            surname_map[parts[-1]] = name

    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    person_aliases = {}

    for i, full_name in enumerate(full_names):
        surname = full_name.split()[-1]
        token = f"PERSON_{alphabet[i]}"
        person_aliases[token] = [full_name, surname]

    return person_aliases
    
def anonymise_news_article(article: str):
    ner_results = ner_pipeline(article)

    # Step 1: extract spans
    person_names = extract_person_spans(article, ner_results)

    # Step 2: build aliases
    person_aliases = build_person_aliases(person_names)

    anonymised = article

    # Step 3: replace FULL NAMES FIRST, then surnames
    for token, aliases in person_aliases.items():
        for alias in sorted(aliases, key=len, reverse=True):
            anonymised = safe_replace(anonymised, alias, token)

    return anonymised, person_aliases