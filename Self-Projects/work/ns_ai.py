import streamlit as st
from datetime import date

# -----------------------------
# Prompt Builder
# -----------------------------

def build_discounting_prompt(
    subject_type,
    client_name,
    client_dob,
    client_gender,
    client_nationality,
    client_profile,
    article_text
):
    client_year = client_dob.year

    prompt = f"""
You are performing name-screening analysis in an Investment & Wealth Management context.
Your task is to evaluate whether a news article is relevant to a client using STRICT discounting protocols.

GLOBAL RULES:
- Evaluate each protocol independently.
- A False Hit (Discounted) conclusion is allowed ONLY if:
  - At least TWO independent discounting factors apply, OR
  - The protocol explicitly allows sole discounting.
- Do NOT assume missing information.
- Cite evidence from both client data and the article.
- Return ONLY valid JSON.

---------------------------------
SUBJECT TYPE
---------------------------------
{subject_type}

---------------------------------
CLIENT SOURCE DATA
---------------------------------
Name: {client_name}
Year of Birth: {client_year}
Gender: {client_gender}
Nationality: {client_nationality}
Profile / Employment: {client_profile}

---------------------------------
NEWS ARTICLE
---------------------------------
{article_text}

---------------------------------
PROTOCOL 0 – ARTICLE SUBJECT ATTRIBUTION
---------------------------------

Determine whether the screened subject is the PRIMARY subject of the article.

Definitions:
- Primary Subject: The article is mainly about this person/entity.
- Secondary Subject: Directly involved in the described events.
- Incidental Mention: Named only in passing, list, comparison, or background context.
  No actions, allegations, or decisions are attributed.

RULE:
- If the screened subject is an INCIDENTAL MENTION,
  this MAY be used as a SOLE discounting factor.

---------------------------------
PROTOCOL 1 – NAME MATCHING
---------------------------------

FOR INDIVIDUALS:
- Name mismatch CAN be sole discount EXCEPT when:
  - Known aliases
  - Transliteration variants (1–2 character variance)
  - Name order differences
- Middle name mismatch → CAN be sole discount

FOR ENTITIES:
- Company suffix differences must be ignored
- Related entities → FLAG as related, NOT discounted

---------------------------------
PROTOCOL 2 – YEAR OF BIRTH
---------------------------------
- Variance ≤ 2 years → cannot be sole discount
- Variance > 2 years → can discount

---------------------------------
PROTOCOL 3 – GENDER
---------------------------------
- Mismatch → can discount

---------------------------------
PROTOCOL 4 – NATIONALITY
---------------------------------
- Cannot be sole discount
- Only usable if no nexus exists
- C/O or P/O Box addresses must NOT be used

---------------------------------
PROTOCOL 5 – PROFILE
---------------------------------
- Cannot be sole discount

---------------------------------
REQUIRED OUTPUT FORMAT (JSON)
---------------------------------

{{
  "article_subject_attribution": {{
    "primary_subjects": ["<names>"],
    "screened_subject_role": "Primary | Secondary | Incidental",
    "can_discount": true/false,
    "reasoning": "Explain with article evidence"
  }},
  "name_matching": {{
    "client_name": "{client_name}",
    "article_name": "<value or Unknown>",
    "assessment": "Match | Mismatch | Possible Alias | Transliteration Variant | Related Entity",
    "can_discount": true/false,
    "reasoning": "Explain"
  }},
  "year_of_birth": {{
    "client_year": {client_year},
    "article_year": "<year or Unknown>",
    "variance": "<number or Unknown>",
    "can_discount": true/false,
    "reasoning": "Explain"
  }},
  "gender": {{
    "client_gender": "{client_gender}",
    "article_gender": "<value or Unknown>",
    "can_discount": true/false,
    "reasoning": "Explain"
  }},
  "nationality": {{
    "client_nationality": "{client_nationality}",
    "article_nationality": "<value or Unknown>",
    "can_discount": true/false,
    "reasoning": "Explain"
  }},
  "profile": {{
    "client_profile": "{client_profile}",
    "article_profile": "<value or Unknown>",
    "can_discount": true/false,
    "reasoning": "Explain"
  }},
  "summary": {{
    "total_discounting_factors": "<number>",
    "final_outcome": "False Hit (Discounted) | Potential Match (Escalate) | Positive Match",
    "overall_explanation": "Clear regulator-ready explanation"
  }}
}}

Return ONLY valid JSON.
"""
    return prompt


# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(page_title="Name Screening – LLM Assist", layout="wide")
st.title("Name Screening – LLM-Assisted Discounting")

st.subheader("Subject Type")
subject_type = st.radio("Select subject type", ["Individual", "Entity"])

st.subheader("Client Source-System Details")

client_name = st.text_input("Client / Entity Name (Full Legal Name)")

col1, col2 = st.columns(2)

with col1:
    client_dob = st.date_input(
        "Date of Birth",
        min_value=date(1900, 1, 1),
        max_value=date.today()
    )
    client_gender = st.selectbox("Gender", ["Male", "Female", "Other", "Unknown"])

with col2:
    client_nationality = st.text_input("Nationality")
    client_profile = st.text_area(
        "Profile / Employment",
        height=120
    )

st.divider()

st.subheader("News Article")
article_text = st.text_area(
    "Paste full news article text here",
    height=300
)

st.divider()

if st.button("Generate LLM Prompt"):
    if not client_name.strip() or not article_text.strip():
        st.error("Client name and article text are mandatory.")
    else:
        prompt = build_discounting_prompt(
            subject_type,
            client_name,
            client_dob,
            client_gender,
            client_nationality,
            client_profile,
            article_text
        )

        st.subheader("Prompt to Send to LLM")
        st.code(prompt, language="text")

        st.info(
            "Send this prompt to your self-hosted LLM API. "
            "Articles where the subject is INCIDENTAL can now be correctly discounted."
        )