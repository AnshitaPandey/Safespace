"""
Sentiment analysis — continuous-ish score via a pretrained RoBERTa sentiment model
(cardiffnlp/twitter-roberta-base-sentiment-latest), exactly the off-the-shelf baseline
recommended in the blueprint. No fine-tuning needed for this one — general sentiment
transfers well across domains, unlike the more app-specific emotion taxonomy.
"""
from functools import lru_cache

from transformers import pipeline

_MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"

# Model outputs "negative"/"neutral"/"positive" with a confidence score; we convert to a
# signed -1..1 scale for easier storage/graphing (matches the `sentiment_score` DB column).
_SIGN_MAP = {"negative": -1, "neutral": 0, "positive": 1}


@lru_cache(maxsize=1)
def _get_pipeline():
    return pipeline("sentiment-analysis", model=_MODEL_NAME)


def predict_sentiment(text: str) -> dict:
    result = _get_pipeline()(text)[0]
    signed_score = _SIGN_MAP[result["label"].lower()] * result["score"]
    return {"label": result["label"].lower(), "confidence": result["score"], "sentiment_score": round(signed_score, 4)}
