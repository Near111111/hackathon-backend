import pickle
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../models/nlp/words-filter.pkl")

# Load once on startup
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

def moderate_content(content: str) -> str:
    """
    Returns: 'safe', 'support_needed', or 'harassment'
    """
    prediction = model.predict([content])
    return prediction[0]