import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from transformers import AutoTokenizer, AutoModelForTokenClassification

MODEL_PATH = "/secure/models/ner-model"

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

model = AutoModelForTokenClassification.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

