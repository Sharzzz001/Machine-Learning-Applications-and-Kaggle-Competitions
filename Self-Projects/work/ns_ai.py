def extract_person_spans(text, ner_results):
    """
    Reconstruct full person names using character offsets.
    Correctly handles WordPiece tokenization and whitespace gaps.
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

        # ✅ ALLOW WHITESPACE GAP
        if start <= span_end + 1:
            span_end = max(span_end, end)
        else:
            persons.append(text[span_start:span_end])
            span_start = start
            span_end = end

    # Final span
    persons.append(text[span_start:span_end])

    # Deduplicate while preserving order
    return list(dict.fromkeys(persons))