def extract_person_spans(text, ner_results):
    """
    Correctly reconstructs person names using character offsets.
    Works with WordPiece tokenization (##).
    """

    # Keep only PER entities
    person_tokens = [
        ent for ent in ner_results
        if ent["entity"].endswith("PER")
    ]

    if not person_tokens:
        return []

    # Sort by character offset
    person_tokens = sorted(person_tokens, key=lambda x: x["start"])

    persons = []
    span_start = person_tokens[0]["start"]
    span_end = person_tokens[0]["end"]

    for ent in person_tokens[1:]:
        start, end = ent["start"], ent["end"]

        # If token touches or overlaps previous → same person
        if start <= span_end:
            span_end = max(span_end, end)
        else:
            persons.append(text[span_start:span_end])
            span_start = start
            span_end = end

    # Final span
    persons.append(text[span_start:span_end])

    # Deduplicate while preserving order
    return list(dict.fromkeys(persons))
    
import string

def anonymise_news_article(article: str):
    ner_results = ner_pipeline(article)

    person_names = extract_person_spans(article, ner_results)

    alphabet = string.ascii_uppercase
    reverse_map = {}
    anonymised = article

    for i, name in enumerate(person_names):
        token = f"PERSON_{alphabet[i]}"
        reverse_map[token] = [name]
        anonymised = anonymised.replace(name, token)

    return anonymised, reverse_map