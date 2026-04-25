import pickle

MODEL_PATH = "models/nlp/words-filter.pkl"

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

test_inputs = [
    "I feel so stressed and overwhelmed",
    "You are stupid and I hate you",
    "I need someone to talk to",
]

for text in test_inputs:
    label = model.predict([text])
    print(f"Input: {text}")
    print(f"Label: {label[0]}\n")