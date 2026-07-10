from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from models.emotion_classifier import predict_emotion
from models.mood_forecaster import predict_mood_forecast
from models.risk_classifier import predict_risk
from models.sentiment import predict_sentiment
from models.topic_detector import predict_topics

app = FastAPI(title="SafeSpace ML Service")


class TextRequest(BaseModel):
    text: str


class MoodHistoryPoint(BaseModel):
    date: str
    score: int


class MoodForecastRequest(BaseModel):
    history: list[dict]  # [{date, score}, ...] — feature engineering happens here, see below


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/predict/emotion")
async def emotion_endpoint(payload: TextRequest):
    return predict_emotion(payload.text)


@app.post("/predict/sentiment")
async def sentiment_endpoint(payload: TextRequest):
    return predict_sentiment(payload.text)


@app.post("/predict/topic")
async def topic_endpoint(payload: TextRequest):
    return predict_topics(payload.text)


@app.post("/predict/risk-classifier")
async def risk_endpoint(payload: TextRequest):
    return predict_risk(payload.text)


@app.post("/predict/mood-forecast")
async def mood_forecast_endpoint(payload: MoodForecastRequest):
    # Minimal feature engineering: mood_score normalized, sentiment/message_count/emotion/topic
    # one-hots default to zero here since the caller (backend) currently only has mood_logs, not
    # full per-day sentiment/topic aggregates. This is the seam where Week 5-6's message-level
    # tagging plugs in richer features once it's populated at scale.
    from models.mood_forecaster import INPUT_SIZE

    feature_sequence = []
    for point in payload.history:
        features = [0.0] * INPUT_SIZE
        features[0] = point.get("score", 5) / 10.0
        feature_sequence.append(features)

    try:
        prediction = predict_mood_forecast(feature_sequence)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {
        "forecast": [{"day_offset": i + 1, "predicted_score": round(v * 10, 1)} for i, v in enumerate(prediction)],
        "model": "gru_v1",
    }
