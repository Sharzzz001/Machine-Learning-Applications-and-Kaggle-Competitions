import json
import re
import pandas as pd
from datetime import datetime
from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein


# =============================================================================
# SECTION 1 - PROMPT GENERATION
# =============================================================================

def generate_extraction_prompt(news_article: str) -> str:
    """
    Build the AI prompt. We only pass the news article (no client PII).
    The AI is asked to return a strict JSON payload.
    """
    prompt = f"""You are a precise information-extraction assistant supporting a compliance name-screening workflow.

Your task: read the news article below and extract every INDIVIDUAL and ENTITY (company / organisation) mentioned.

OUTPUT FORMAT (return ONLY valid JSON, no prose, no markdown fences)
---------------------------------------------------------------------
{{
  "individuals": [
    {{
      "full_name":     "<full name as written in article>",
      "aliases":       ["<any other names / nicknames used for this person in the article>"],
      "age":           <integer, or null if not stated>,
      "nationality":   "<country or null>",
      "gender":        "Male" | "Female" | null,
      "profile":       "<concise description: role, title, employer, known activities>",
      "mention_type":  "PRIMARY" | "SECONDARY" | "INCIDENTAL",
      "article_evidence": {{
        "age":          "<exact quote or phrase from the article supporting the age, e.g. aged 45 or born in 1978. Use Not mentioned if absent.>",
        "nationality":  "<exact quote or phrase from the article supporting nationality. Use Not mentioned if absent.>",
        "gender":       "<exact quote or phrase supporting gender inference, e.g. pronoun he, title Mr. Use Not mentioned if absent.>",
        "profile":      "<exact quote or phrase from the article supporting the role/employment/activities described.>",
        "mention_type": "<exact quote or phrase that best illustrates how prominently this person features in the article.>"
      }}
    }}
  ],
  "entities": [
    {{
      "entity_name":   "<name as written>",
      "aliases":       ["<other names / abbreviations used in the article>"],
      "entity_type":   "<company | NGO | government body | other>",
      "profile":       "<concise description of what this entity is / does>",
      "mention_type":  "PRIMARY" | "SECONDARY" | "INCIDENTAL",
      "article_evidence": {{
        "profile":      "<exact quote or phrase from the article supporting what this entity is / does.>",
        "mention_type": "<exact quote or phrase that best illustrates how prominently this entity features in the article.>"
      }}
    }}
  ]
}}

DEFINITIONS FOR mention_type
------------------------------
PRIMARY    - The article is primarily ABOUT this person/entity.
SECONDARY  - This person/entity is directly involved in the events described
             (actions, allegations, decisions are attributed to them).
INCIDENTAL - Named only in passing, in a list, comparison, or background
             context. No actions, allegations, or decisions are attributed.

IMPORTANT RULES
----------------
- Include EVERY named person and organisation, no matter how briefly mentioned.
- For age: extract from text (e.g. aged 45, 45-year-old) or calculate from
  any stated birth year. Return null if unknown.
- For gender: infer from pronouns or titles if not explicitly stated.
- article_evidence values must be short direct quotes from the article text.
  Do NOT paraphrase - copy the relevant fragment verbatim.
- Return ONLY the JSON object. Do not add markdown fences or explanatory text.

NEWS ARTICLE
-------------
{news_article}
"""
    return prompt.strip()


# =============================================================================
# SECTION 2 - AI API CALL  (fill in your implementation)
# =============================================================================

def call_ai_api(prompt: str) -> str:
    """
    Send prompt to your LLM API and return the raw response string.

    Replace the body below with your actual API call, for example:
    ------------------------------------------------------------------
    import anthropic
    client = anthropic.Anthropic(api_key="YOUR_KEY")
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
    ------------------------------------------------------------------
    """
    raise NotImplementedError("Implement your API call here.")


# =============================================================================
# SECTION 3 - JSON CLEANING & PARSING
# =============================================================================

def clean_and_parse_json(raw: str) -> dict:
    """
    Robustly clean a raw LLM string and parse it to a dict.

    Handles the most common LLM JSON failure modes:
      - Markdown fences (```json ... ```)
      - Windows-style line endings
      - Trailing commas before closing brackets  (e.g. {..., } or [..., ])
      - ASCII control characters that break the parser
      - Prose before/after the JSON block
    """
    text = raw.strip()

    # 1. Strip markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # 2. Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 3. Remove ASCII control characters (except tab \x09 and newline \x0a)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 4. Remove trailing commas before } or ] (invalid in JSON)
    text = re.sub(r",\s*(\})", r"\1", text)
    text = re.sub(r",\s*(\])", r"\1", text)

    # 5. First attempt: parse cleaned text as-is
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 6. Second attempt: extract the outermost { ... } block
    #    in case the model added prose before/after the JSON
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # 7. Last resort: raise with a helpful message showing the raw output
    raise ValueError(
        f"Could not parse LLM output as JSON.\n"
        f"--- RAW OUTPUT (first 500 chars) ---\n{raw[:500]}"
    )


# =============================================================================
# SECTION 4 - UTILITIES
# =============================================================================

def calculate_age(dob) -> int | None:
    """Convert DOB (any parseable format) to current age in years."""
    if dob is None or (isinstance(dob, float) and pd.isna(dob)):
        return None
    try:
        if not isinstance(dob, datetime):
            dob = pd.to_datetime(dob)
        today = datetime.today()
        return today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )
    except Exception:
        return None


_COMPANY_SUFFIX_RE = re.compile(
    r'\b(ltd\.?|limited|inc\.?|incorporated|llc|llp|plc|corp\.?|'
    r'corporation|gmbh|ag|sa|bv|nv|pte\.?|co\.?|pty\.?)\b',
    re.IGNORECASE,
)

def _strip_suffixes(name: str) -> str:
    return _COMPANY_SUFFIX_RE.sub('', name).strip().lower()


def name_fuzzy_score(name_a: str, name_b: str) -> float:
    """
    Multi-strategy fuzzy score (0-100) handling:
      - Word order differences  (token_sort_ratio)
      - Subset names            (token_set_ratio)
      - Partial name matches    (partial_ratio)
    Returns the maximum across all strategies.
    """
    a, b = name_a.lower().strip(), name_b.lower().strip()
    return max(
        fuzz.token_sort_ratio(a, b),
        fuzz.token_set_ratio(a, b),
        fuzz.partial_ratio(a, b),
    )


def char_edit_distance(name_a: str, name_b: str) -> int:
    """Levenshtein distance - used to spot 1-2 char transliteration variants."""
    return Levenshtein.distance(name_a.lower(), name_b.lower())


_GENDER_MAP = {
    'm': 'male', 'f': 'female',
    'male': 'male', 'female': 'female',
    'man': 'male', 'woman': 'female',
    'mr': 'male', 'mrs': 'female', 'ms': 'female', 'miss': 'female',
}

def is_unknown(value) -> bool:
    """Return True if a source-system value is missing or explicitly Unknown."""
    return str(value).strip().lower() in ("unknown", "", "nan", "none", "n/a", "na")


def normalise_gender(raw: str) -> str | None:
    return _GENDER_MAP.get(str(raw).strip().lower())


# =============================================================================
# SECTION 5 - MATCH FINDER
# =============================================================================

# Tune these thresholds as needed
NAME_MATCH_THRESHOLD   = 80   # fuzzy score to consider a name match
TRANSLITERATION_CHARS  = 2    # max edit distance for transliteration leniency
PROFILE_SIMILARITY_MIN = 45   # below this = profile mismatch flag
NATIONALITY_SIM_MIN    = 65   # below this = nationality mismatch flag

def find_best_match(subject_name: str, subject_type: str, ai_output: dict):
    """
    Search the AI output for the best matching individual or entity.
    For entities we strip company suffixes before comparing.

    Returns (matched_record: dict | None, best_score: float)
    """
    pool = (
        ai_output.get("individuals", [])
        if subject_type.strip().lower() == "individual"
        else ai_output.get("entities", [])
    )

    is_entity = subject_type.strip().lower() != "individual"
    name_key  = "entity_name" if is_entity else "full_name"

    subject_cmp = _strip_suffixes(subject_name) if is_entity else subject_name

    best_match, best_score = None, 0.0

    for record in pool:
        candidates = [record.get(name_key, "")] + record.get("aliases", [])
        for candidate in candidates:
            if not candidate:
                continue
            cmp_candidate = _strip_suffixes(candidate) if is_entity else candidate
            score = name_fuzzy_score(subject_cmp, cmp_candidate)
            if score > best_score:
                best_score = score
                best_match = record

    return best_match, best_score


# =============================================================================
# SECTION 6 - DISCOUNTING ENGINE  (Protocols 0-5)
# =============================================================================

def apply_discounting_rules(row: pd.Series, ai_output: dict) -> dict:
    """
    Apply Protocols 0-5 to decide DISCOUNTED or ESCALATE.

    Returns a dict:
    {
        "subject_name":           str,
        "result":                 "DISCOUNTED" | "ESCALATE" | "NO_MATCH",
        "discount_reasons":       [str],
        "soft_flags":             [str],
        "match_score":            float,
        "matched_article_record": dict | None,
    }
    """
    subject_name        = str(row.get("Name", "")).strip()
    subject_type        = str(row.get("SubjectType", "Individual")).strip()
    subject_dob         = row.get("DOB")
    subject_nationality = str(row.get("Nationality", "") or "").strip()
    subject_gender_raw  = str(row.get("Gender", "") or "").strip()
    subject_profile     = str(row.get("Profile / Employment", "") or "").strip().lower()
    subject_age         = calculate_age(subject_dob)
    subject_gender      = normalise_gender(subject_gender_raw)

    out = {
        "subject_name":           subject_name,
        "result":                 None,
        "discount_reasons":       [],
        "soft_flags":             [],
        "match_score":            0.0,
        "matched_article_record": None,
    }

    # Find best match
    matched, score = find_best_match(subject_name, subject_type, ai_output)
    out["match_score"]            = score
    out["matched_article_record"] = matched

    # PROTOCOL 1 - NAME MATCHING
    if matched is None:
        out["result"] = "NO_MATCH"
        out["discount_reasons"].append("PROTOCOL 1: Subject name not found in article at all.")
        return out

    if score < NAME_MATCH_THRESHOLD:
        name_key  = "entity_name" if subject_type.strip().lower() != "individual" else "full_name"
        edit_dist = char_edit_distance(subject_name, matched.get(name_key, ""))
        if edit_dist > TRANSLITERATION_CHARS:
            out["result"] = "DISCOUNTED"
            out["discount_reasons"].append(
                f"PROTOCOL 1: Name mismatch (fuzzy={score:.0f}/100, "
                f"edit_distance={edit_dist}). "
                f"Client='{subject_name}' | Article='{matched.get(name_key, '')}'."
            )
            return out

    mention_type = str(matched.get("mention_type", "")).upper()

    # PROTOCOL 0 - INCIDENTAL MENTION (sole discount)
    if mention_type == "INCIDENTAL":
        out["result"] = "DISCOUNTED"
        out["discount_reasons"].append(
            "PROTOCOL 0: Subject is an INCIDENTAL mention only - "
            "no actions, allegations, or decisions attributed."
        )
        return out

    # PROTOCOL 3 - GENDER (sole discount for individuals)
    if subject_type.strip().lower() == "individual":
        if is_unknown(subject_gender_raw):
            out["soft_flags"].append("PROTOCOL 3: Skipped - gender is Unknown in source system.")
        else:
            article_gender = normalise_gender(str(matched.get("gender", "") or ""))
            if subject_gender and article_gender and subject_gender != article_gender:
                out["result"] = "DISCOUNTED"
                out["discount_reasons"].append(
                    f"PROTOCOL 3: Gender mismatch - "
                    f"client='{subject_gender}', article='{article_gender}'."
                )
                return out

    # Accumulate soft-discount factors
    soft = out["soft_flags"]

    # PROTOCOL 2 - YEAR OF BIRTH
    article_age = matched.get("age")
    if is_unknown(str(row.get("DOB", ""))):
        soft.append("PROTOCOL 2: Skipped - DOB is Unknown in source system.")
    elif subject_age is not None and article_age is not None:
        age_diff = abs(subject_age - article_age)
        if age_diff > 2:
            soft.append(
                f"PROTOCOL 2: Age variance > 2 years "
                f"(client={subject_age}, article={article_age}, diff={age_diff})."
            )

    # PROTOCOL 4 - NATIONALITY (cannot be sole discount)
    article_nationality = str(matched.get("nationality", "") or "").strip()
    if is_unknown(subject_nationality):
        soft.append("PROTOCOL 4: Skipped - nationality is Unknown in source system.")
    elif subject_nationality and article_nationality:
        nat_score = name_fuzzy_score(subject_nationality, article_nationality)
        if nat_score < NATIONALITY_SIM_MIN:
            soft.append(
                f"PROTOCOL 4: Nationality mismatch - "
                f"client='{subject_nationality}', article='{article_nationality}' "
                f"(similarity={nat_score:.0f}/100)."
            )

    # PROTOCOL 5 - PROFILE (cannot be sole discount)
    article_profile = str(matched.get("profile", "") or "").lower()
    if is_unknown(subject_profile):
        soft.append("PROTOCOL 5: Skipped - profile is Unknown in source system.")
    elif subject_profile and article_profile:
        prof_score = name_fuzzy_score(subject_profile, article_profile)
        if prof_score < PROFILE_SIMILARITY_MIN:
            soft.append(
                f"PROTOCOL 5: Profile mismatch - "
                f"client='{subject_profile[:60]}...', "
                f"article='{article_profile[:60]}...' "
                f"(similarity={prof_score:.0f}/100)."
            )

    # 2+ soft factors together can discount
    if len(soft) >= 2:
        out["result"] = "DISCOUNTED"
        out["discount_reasons"].extend(soft)
    else:
        out["result"] = "ESCALATE"

    return out


# =============================================================================
# SECTION 7 - MAIN PIPELINE
# =============================================================================

def process_screening_file(
    input_path: str,
    output_path: str = "screening_results.csv",
    article_col: str = "News Article",
):
    """
    End-to-end pipeline.

    Reads input_path CSV -> generates prompts -> calls AI -> parses JSON
    -> applies discounting -> writes output_path CSV.
    """
    df = pd.read_csv(input_path)
    records = []

    for idx, row in df.iterrows():
        news_article = str(row.get(article_col, "")).strip()
        subject_name = str(row.get("Name", f"Row {idx}"))

        print(f"[{idx+1}/{len(df)}] Processing: {subject_name}")

        # Step 1: Generate prompt (article only)
        prompt = generate_extraction_prompt(news_article)

        # Step 2a: Call AI API
        try:
            ai_raw = call_ai_api(prompt)
        except NotImplementedError:
            print("  WARNING: call_ai_api() not implemented - skipping row.")
            records.append({
                **row.to_dict(),
                "screening_result":       "ERROR",
                "discount_reasons":       "API not implemented",
                "soft_flags":             "",
                "match_score":            "",
                "matched_article_record": "",
                "llm_raw_output":         "",
            })
            continue
        except Exception as exc:
            print(f"  ERROR - API call failed: {exc}")
            records.append({
                **row.to_dict(),
                "screening_result":       "ERROR",
                "discount_reasons":       f"API error: {exc}",
                "soft_flags":             "",
                "match_score":            "",
                "matched_article_record": "",
                "llm_raw_output":         "",
            })
            continue

        # Step 2b: Parse JSON - separate block so errors are clearly labelled
        raw_ai_output = ai_raw if isinstance(ai_raw, str) else json.dumps(ai_raw)
        try:
            if isinstance(ai_raw, str):
                ai_output = clean_and_parse_json(ai_raw)
            else:
                ai_output = ai_raw  # already a dict
        except Exception as exc:
            print(f"  ERROR - JSON parse failed: {exc}")
            records.append({
                **row.to_dict(),
                "screening_result":       "ERROR",
                "discount_reasons":       f"JSON parse error: {exc}",
                "soft_flags":             "",
                "match_score":            "",
                "matched_article_record": "",
                "llm_raw_output":         raw_ai_output,  # save raw for debugging
            })
            continue

        # Step 3: Local discounting
        result = apply_discounting_rules(row, ai_output)
        print(f"  -> {result['result']}  |  reasons: {result['discount_reasons']}")

        records.append({
            **row.to_dict(),
            "screening_result":       result["result"],
            "discount_reasons":       " | ".join(result["discount_reasons"]),
            "soft_flags":             " | ".join(result["soft_flags"]),
            "match_score":            round(result["match_score"], 1),
            "matched_article_record": json.dumps(result["matched_article_record"]),
            "llm_raw_output":         raw_ai_output,
        })

    out_df = pd.DataFrame(records)
    out_df.to_csv(output_path, index=False)
    print(f"\nResults written to: {output_path}")
    return out_df


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import sys
    input_file  = sys.argv[1] if len(sys.argv) > 1 else "screening_input.csv"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "screening_results.csv"
    process_screening_file(input_file, output_file)