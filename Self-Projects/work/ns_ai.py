import streamlit as st
from datetime import datetime

# -----------------------------
# Prompt Builder
# -----------------------------

def build_discounting_prompt(
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

IMPORTANT RULES:
- You MUST evaluate each protocol independently.
- No single factor may be used to discount a hit on its own unless explicitly permitted.
- A False Hit (Discounted) conclusion is allowed ONLY if at least TWO independent discounting factors apply,
  except where explicitly stated.
- You MUST explain reasoning using evidence from both client data and the article.
- If information is missing in the article, state "Unknown" and do not assume.

---------------------------------
CLIENT SOURCE DATA
---------------------------------
Year of Birth: {client_year}
Gender: {client_gender}
Nationality: {client_nationality}
Profile / Employment (free text): {client_profile}

---------------------------------
NEWS ARTICLE
---------------------------------
{article_text}

---------------------------------
DISCOUNTING PROTOCOLS
---------------------------------

1. YEAR OF BIRTH
- If variance ≤ 2 years: CANNOT be used as a sole discounting factor.
- If variance > 2 years: CAN be used as a discounting factor.

2. GENDER
- If mismatch: CAN be used as a discounting factor.

3. NATIONALITY
- CANNOT be used as a sole discounting factor.
- May only contribute if there is sufficient information that the subject has NO nexus to the countries mentioned.
- C/O or P/O Box addresses MUST NOT be used.
- Consider historical nationality if mentioned.

4. PROFILE OF SUBJECT
- CANNOT be used as a sole discounting factor.
- Clients may have multiple or changing roles over time.

---------------------------------
REQUIRED OUTPUT FORMAT (JSON ONLY)
---------------------------------

{{
  "year_of_birth": {{
    "client_year": {client_year},
    "article_year": "<year or Unknown>",
    "variance": "<number or Unknown>",
    "can_discount": true/false,
    "reasoning": "Explain strictly per protocol"
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
    "reasoning": "Explain including nexus assessment"
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
    "overall_explanation": "Clear, regulator-ready explanation"
  }}
}}

Return ONLY valid JSON. Do not include any commentary outside JSON.
"""
    return prompt


# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(page_title="Name Screening – LLM Assist", layout="wide")
st.title("Name Screening – LLM-Assisted Discounting")

st.subheader("Client Source-System Details")

col1, col2 = st.columns(2)

with col1:
    client_dob = st.date_input("Date of Birth")
    client_gender = st.selectbox("Gender", ["Male", "Female", "Other", "Unknown"])

with col2:
    client_nationality = st.text_input("Nationality")
    client_profile = st.text_area(
        "Profile / Employment History",
        height=120,
        placeholder="Free-text employment or profile description"
    )

st.divider()

st.subheader("News Article")
article_text = st.text_area(
    "Paste full news article text here",
    height=300
)

st.divider()

if st.button("Generate LLM Prompt"):
    if not article_text.strip():
        st.error("Please paste a news article.")
    else:
        prompt = build_discounting_prompt(
            client_dob=client_dob,
            client_gender=client_gender,
            client_nationality=client_nationality,
            client_profile=client_profile,
            article_text=article_text
        )

        st.subheader("Prompt to Send to LLM")
        st.code(prompt, language="text")

        st.info(
            "Send the above prompt to your self-hosted LLM API. "
            "The response should be parsed as JSON and rendered in a structured UI."
        )