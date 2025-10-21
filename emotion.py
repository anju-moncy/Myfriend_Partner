from transformers import pipeline

# Load model once at startup
classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=1,
)


def detect_emotion(text):
    if not text.strip():
        return "neutral"
    result = classifier(text)[0]
    return result["label"]
