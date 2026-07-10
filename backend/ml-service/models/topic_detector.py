"""
Topic detection — multi-label zero-shot classification over the 7 topics (relationships,
career, academics, family, stress, health, personal growth), exactly as the blueprint
recommends as the starting point before a dedicated fine-tuned classifier: an NLI-based
zero-shot model needs no labeled data and works immediately, since it works by testing
"this text is about {topic}" as an entailment hypothesis against the message.
"""
from functools import lru_cache

from transformers import pipeline

_MODEL_NAME = "facebook/bart-large-mnli"
_TOPICS = ["relationships", "career", "academics", "family", "stress", "health", "personal growth"]
_THRESHOLD = 0.5  # a message can match zero, one, or several topics


@lru_cache(maxsize=1)
def _get_pipeline():
    return pipeline("zero-shot-classification", model=_MODEL_NAME)


def predict_topics(text: str) -> dict:
    result = _get_pipeline()(text, candidate_labels=_TOPICS, multi_label=True)
    matched = [
        {"topic": label, "score": round(score, 4)}
        for label, score in zip(result["labels"], result["scores"])
        if score >= _THRESHOLD
    ]
    return {"topics": matched}
