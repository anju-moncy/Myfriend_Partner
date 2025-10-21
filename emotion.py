from transformers import pipeline

# Load model once at startup (default returns best label dict)
classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
)


def detect_emotion(text: str) -> str:
    if not text or not text.strip():
        return "neutral"
    results = classifier(text)
    # Handle both shapes: list-of-dicts or list-of-list-of-dicts
    if isinstance(results, list):
        first = results[0]
        if isinstance(first, dict):
            return first.get("label", "neutral")
        if isinstance(first, list) and first:
            top_pred = first[0]
            if isinstance(top_pred, dict):
                return top_pred.get("label", "neutral")
    return "neutral"
