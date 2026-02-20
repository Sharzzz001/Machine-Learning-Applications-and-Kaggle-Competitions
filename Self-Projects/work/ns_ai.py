from transformers import AutoTokenizer, AutoModel

MODEL_PATH = "/internal/path/coref-spanbert-large"

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

model = AutoModel.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)