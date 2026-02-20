def build_person_aliases(person_names):
    """
    Returns:
    {
      "PERSON_A": ["Puris", "Katie Puris"],
      "PERSON_B": ["Matthews", "John Matthews"]
    }
    """
    canonical = []
    surname_map = {}

    # First pass: identify full names
    for name in person_names:
        parts = name.split()
        if len(parts) >= 2:
            canonical.append(name)
            surname_map[parts[-1]] = name

    # Assign PERSON tokens
    person_aliases = {}
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    for i, full_name in enumerate(canonical):
        token = f"PERSON_{alphabet[i]}"
        aliases = [full_name]

        surname = full_name.split()[-1]
        aliases.insert(0, surname)  # surname FIRST

        person_aliases[token] = aliases

    return person_aliases
    
def anonymise_news_article(article: str):
    ner_results = ner_pipeline(article)

    # Step 1: extract spans
    person_names = extract_person_spans(article, ner_results)

    # Step 2: build alias map
    person_aliases = build_person_aliases(person_names)

    anonymised = article

    # Step 3: replace aliases (short → long)
    for token, aliases in person_aliases.items():
        for alias in sorted(aliases, key=len):  # surname first
            anonymised = anonymised.replace(alias, token)

    return anonymised, person_aliases