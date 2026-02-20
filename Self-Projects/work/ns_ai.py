from fastcoref import FCoref

coref = FCoref(device="cpu")  # or "cuda"

text = """
Katie Puris said she would respond to the allegations.
After Puris’ initial claim, she clarified her position.
"""

preds = coref.predict(
    texts=[text]
)