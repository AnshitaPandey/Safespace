"""
Emotion classification — predicts one of: happy, sad, angry, anxious, lonely, neutral,
excited, frustrated (the 8-label taxonomy from the PRD).

PRAGMATIC DEFAULT vs. the blueprint's plan: the blueprint calls for fine-tuning
distilroberta-base on GoEmotions/EmpatheticDialogues. That requires a labeled dataset and a
training run (see ../training/train_emotion_classifier.py for that exact pipeline). Until
that's been run, this module uses a strong off-the-shelf checkpoint
(j-hartmann/emotion-english-distilroberta-base, trained on Ekman's 6 emotions + neutral) and
maps its output onto our 8 labels. This is a real, working classifier — just not yet
fine-tuned on our specific taxonomy/domain.
"""
from functools import lru_cache

from transformers import pipeline

_MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"

# Ekman label -> our taxonomy. "surprise" and "disgust" don't map cleanly to a single one of
# our 8 labels; surprise leans toward excited, disgust toward frustrated, as the closest fit.
_LABEL_MAP = {
    "joy": "happy",
    "sadness": "sad",
    "anger": "angry",
    "fear": "anxious",
    "neutral": "neutral",
    "surprise": "excited",
    "disgust": "frustrated",
}


@lru_cache(maxsize=1)
def _get_pipeline():
    return pipeline("text-classification", model=_MODEL_NAME, top_k=None)


def predict_emotion(text: str) -> dict:
    results = _get_pipeline()(text)[0]  # list of {label, score} across all classes
    mapped_scores: dict[str, float] = {}
    for item in results:
        mapped_label = _LABEL_MAP.get(item["label"], "neutral")
        mapped_scores[mapped_label] = mapped_scores.get(mapped_label, 0.0) + item["score"]

    # "lonely" has no direct source label in the underlying model — it's the one gap this
    # pragmatic default can't cover well; the fine-tuning script closes this gap once trained.
    top_label = max(mapped_scores, key=mapped_scores.get)
    return {"emotion": top_label, "scores": mapped_scores}
