import streamlit as st

# -----------------------------
# Prompt Builder – ARTICLE ONLY
# -----------------------------

def build_article_intelligence_prompt(subject_type, article_text):
    prompt = f"""
You are performing NEWS ARTICLE INTELLIGENCE EXTRACTION in an
Investment & Wealth Management name-screening context.

IMPORTANT:
- The client is UNKNOWN to you.
- DO NOT attempt to match, discount, or assess relevance to any client.
- DO NOT make screening or compliance decisions.
- Your role is ONLY to extract what the article explicitly states
  or reasonably infers using the rules below.
- Return ONLY valid JSON.

---------------------------------
SUBJECT TYPE
---------------------------------
{subject_type}

---------------------------------
NEWS ARTICLE
---------------------------------
{article_text}

---------------------------------
PROTOCOL 0 – ARTICLE SUBJECT ATTRIBUTION
---------------------------------

Identify ALL identifiable subjects mentioned in the article.

For each subject, classify their role as:
- Primary Subject
- Secondary Subject
- Incidental Mention

Definitions:
- Primary: The article is mainly about this subject.
- Secondary: Directly involved in the events described.
- Incidental: Mentioned only in passing, lists, or background context.

---------------------------------
PROTOCOL 1 – NAME IDENTIFICATION
---------------------------------

For each subject:
- Extract the FULL NAME exactly as stated in the article.
- If unclear or unnamed, return "Unknown".

---------------------------------
PROTOCOL 2 – AGE / YEAR OF BIRTH
---------------------------------

For each subject:
- Extract Year of Birth if explicitly stated.
- If age is stated (e.g., "aged 24"):
  - Infer Year of Birth using the article year.
- Use the article year if explicitly stated or clearly implied.
- If the article year cannot be determined, return "Unknown".
- Do NOT guess age or year of birth from role, seniority, or appearance.

---------------------------------
PROTOCOL 3 – GENDER
---------------------------------

For each subject:
- Extract gender if:
  - Explicitly stated (male, female), OR
  - Clearly inferable from pronouns (he / she / his / her), OR
  - Clearly inferable from titles (Mr / Ms).
- Do NOT infer gender from name alone.
- If unclear, return "Unknown".

---------------------------------
PROTOCOL 4 – NATIONALITY
---------------------------------

For each subject:
- Extract nationality ONLY if explicitly stated.
- Do NOT infer nationality from location, residence, or name.
- Otherwise return "Unknown".

---------------------------------
PROTOCOL 5 – PROFILE / ROLE
---------------------------------

For each subject:
- Extract profession, role, or public profile if stated
  (e.g., politician, businessman, student).
- Otherwise return "Unknown".

---------------------------------
REQUIRED OUTPUT FORMAT (JSON)
---------------------------------

{{
  "subjects": [
    {{
      "name": "<string or Unknown>",
      "article_subject_role": "Primary | Secondary | Incidental",
      "year_of_birth": "<year or Unknown>",
      "gender": "<value or Unknown>",
      "nationality": "<value or Unknown>",
      "profile": "<value or Unknown>",
      "article_evidence": "Quote or paraphrase supporting the extraction"
    }}
  ],
  "article_summary": "One-paragraph neutral summary of the article"
}}

Return ONLY valid JSON.
"""
    return prompt


# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(
    page_title="Name Screening – Article Intelligence",
    layout="wide"
)

st.title("Name Screening – LLM Article Intelligence Prompt Generator")

st.subheader("Subject Type")
subject_type = st.radio(
    "Select subject type",
    ["Individual", "Entity"]
)

st.divider()

st.subheader("News Article")
article_text = st.text_area(
    "Paste full news article text here",
    height=350,
    placeholder="Paste the complete article text here..."
)

st.divider()

if st.button("Generate LLM Prompt"):
    if not article_text.strip():
        st.error("Article text is mandatory.")
    else:
        prompt = build_article_intelligence_prompt(
            subject_type,
            article_text
        )

        st.subheader("Prompt to Send to LLM")
        st.code(prompt, language="text")

        st.info(
            "This prompt is designed for Bedrock / self-hosted LLMs. "
            "It extracts ONLY article intelligence. "
            "Client matching and discounting must be performed locally."
        )