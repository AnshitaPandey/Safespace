"""
Mood forecasting — GRU model, per the blueprint's architecture comparison (GRU chosen as the
starting point over LSTM/Transformer because per-user history is short early on; a GRU
converges faster and overfits less with limited data. See ../training/train_mood_forecaster.py
for the training pipeline and for the LSTM/Transformer variants to compare against once more
data exists).

This module defines the real model architecture and a predict function. No checkpoint ships
with this repo — there's no training data yet. If MOOD_FORECASTER_CHECKPOINT isn't found, the
API layer returns 503 and the backend's analytics endpoint falls back to a naive moving-average
forecast (see backend/app/api/v1/analytics.py) rather than serving a nonsense prediction from
random-initialized weights.
"""
import os

import torch
import torch.nn as nn

CHECKPOINT_PATH = os.environ.get("MOOD_FORECASTER_CHECKPOINT", "/app/checkpoints/mood_forecaster_gru.pt")

# Features per timestep, matching the blueprint: mood_score, sentiment_score, message_count,
# dominant_emotion (one-hot, 8 classes), dominant_topic (one-hot, 7 classes) = 3 + 8 + 7 = 18
INPUT_SIZE = 18
HIDDEN_SIZE = 32
FORECAST_HORIZON = 3  # predict next 3 days


class MoodForecasterGRU(nn.Module):
    def __init__(self, input_size: int = INPUT_SIZE, hidden_size: int = HIDDEN_SIZE, horizon: int = FORECAST_HORIZON):
        super().__init__()
        self.gru = nn.GRU(input_size=input_size, hidden_size=hidden_size, num_layers=2, batch_first=True, dropout=0.2)
        self.head = nn.Linear(hidden_size, horizon)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, input_size)
        _, hidden = self.gru(x)
        last_hidden = hidden[-1]  # (batch, hidden_size)
        return self.head(last_hidden)  # (batch, horizon) -- predicted mood scores


_model_cache: MoodForecasterGRU | None = None


def _load_model() -> MoodForecasterGRU:
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    if not os.path.exists(CHECKPOINT_PATH):
        raise FileNotFoundError(
            f"No trained checkpoint at {CHECKPOINT_PATH}. Run training/train_mood_forecaster.py first."
        )

    model = MoodForecasterGRU()
    model.load_state_dict(torch.load(CHECKPOINT_PATH, map_location="cpu"))
    model.eval()
    _model_cache = model
    return model


def predict_mood_forecast(feature_sequence: list[list[float]]) -> list[float]:
    """feature_sequence: list of per-day feature vectors (len INPUT_SIZE each), oldest first."""
    model = _load_model()  # raises FileNotFoundError if untrained — caller should catch and 503
    with torch.no_grad():
        x = torch.tensor([feature_sequence], dtype=torch.float32)  # (1, seq_len, input_size)
        prediction = model(x)
        return prediction.squeeze(0).tolist()
