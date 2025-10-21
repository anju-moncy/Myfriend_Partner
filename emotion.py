from transformers import pipeline

# Load model once at startup
classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
)


def detect_emotion(text):
    if not text.strip():
        return "neutral"
    result = classifier(text)
    # Default output is a list of dicts; take top prediction
    top = result[0] if isinstance(result, list) and result else {"label": "neutral"}
    return top.get("label", "neutral")
