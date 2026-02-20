def normalise_for_key(name: str) -> str:
    """
    Normalise name ONLY for identity resolution.
    Titles are removed here, but NOT from the article text.
    """
    name = name.lower().strip()

    titles = ["mr ", "ms ", "mrs ", "dr ", "prof "]
    for t in titles:
        if name.startswith(t):
            name = name[len(t):]

    return name
    

import spacy
import string

nlp = spacy.load("en_core_web_sm")

def anonymise_article_entities(text):
    doc = nlp(text)

    entity_map = {}
    person_counter = 0
    alphabet = string.ascii_uppercase
    anonymised_text = text

    entities = sorted(
        [ent for ent in doc.ents if ent.label_ == "PERSON"],
        key=lambda e: e.start_char,
        reverse=True
    )

    for ent in entities:
        surface_form = ent.text
        key = normalise_for_key(surface_form)

        if key not in entity_map:
            entity_map[key] = f"PERSON_{alphabet[person_counter]}"
            person_counter += 1

        anonymised_text = (
            anonymised_text[:ent.start_char]
            + anonymised_text[ent.end_char:]
        )
        anonymised_text = (
            anonymised_text[:ent.start_char]
            + surface_form.replace(
                surface_form.split()[-1],
                entity_map[key]
            )
            + anonymised_text[ent.start_char:]
        )

    return anonymised_text, entity_map