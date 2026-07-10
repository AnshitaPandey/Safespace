"""
Risk classifier for the safety layer (Week 7-8 upgrade). The blueprint's plan is to fine-tune
a dedicated model on labeled crisis-language data once it exists. Until there's a labeled
dataset to train on, this uses zero-shot NLI classification as a pragmatic stand-in — it will
be noisier than a purpose-trained model, which is exactly why `app/ai/safety_layer.py` on the
backend treats this as a supplement to the keyword gate (takes the max of the two), never a
replacement. The keyword gate remains the deterministic backstop regardless of what this
model outputs.
"""
from functools import lru_cache

from transformers import pipeline

_MODEL_NAME = "facebook/bart-large-mnli"

_HYPOTHESES = {
    "high": "This message expresses suicidal thoughts or intent to self-harm.",
    "medium": "This message expresses significant emotional distress or hopelessness.",
    "none": "This is an ordinary message with no signs of crisis.",
}


@lru_cache(maxsize=1)
def _get_pipeline():
    return pipeline("zero-shot-classification", model=_MODEL_NAME)


def predict_risk(text: str) -> dict:
    labels = list(_HYPOTHESES.keys())
    hypothesis_template = "{}"  # we pass full hypotheses as labels directly
    result = _get_pipeline()(text, candidate_labels=[_HYPOTHESES[k] for k in labels])

    # Map the winning hypothesis sentence back to its risk-level key.
    reverse_map = {v: k for k, v in _HYPOTHESES.items()}
    top_label = reverse_map[result["labels"][0]]
    top_score = result["scores"][0]

    # Require a reasonably confident top prediction before elevating risk — an uncertain
    # zero-shot call shouldn't override "none" lightly.
    if top_label != "none" and top_score < 0.6:
        top_label = "none"

    return {"risk_level": top_label, "confidence": round(top_score, 4)}
