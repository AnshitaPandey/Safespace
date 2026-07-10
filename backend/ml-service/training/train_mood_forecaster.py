"""
Trains the mood-forecasting model on historical per-user mood_logs (+ derived features), and
compares GRU vs. LSTM vs. a small Transformer encoder — the architecture comparison called for
in the blueprint. Run manually once enough real user data exists:

    python train_mood_forecaster.py --data_source postgres --epochs 30

Until then, `--data_source synthetic` generates a plausible synthetic dataset so this script
is runnable and demonstrates the full pipeline (useful for a portfolio walkthrough even before
real user data accumulates).

Evaluation: MAE/RMSE on held-out future mood scores, plus "direction accuracy" (did the model
correctly predict trending up vs. down), since that's the more actionable metric for the
user-facing weekly report even when the exact score is off.
"""
import argparse

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, random_split

SEQ_LEN = 14         # two weeks of history per training example
FORECAST_HORIZON = 3  # predict next 3 days
INPUT_SIZE = 18       # mood_score, sentiment_score, message_count, emotion one-hot(8), topic one-hot(7)


class MoodSequenceDataset(Dataset):
    def __init__(self, sequences: np.ndarray, targets: np.ndarray):
        self.sequences = torch.tensor(sequences, dtype=torch.float32)
        self.targets = torch.tensor(targets, dtype=torch.float32)

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], self.targets[idx]


def generate_synthetic_data(n_users: int = 200, days_per_user: int = 60) -> tuple[np.ndarray, np.ndarray]:
    """Generates plausible mood trajectories (slow drift + noise + weekly seasonality) purely
    so this script is runnable end-to-end without a real database. Replace with
    `load_from_postgres()` once you have real longitudinal data."""
    rng = np.random.default_rng(42)
    sequences, targets = [], []

    for _ in range(n_users):
        baseline = rng.uniform(4, 7)
        drift = rng.uniform(-0.02, 0.02)
        days = np.arange(days_per_user)
        weekly = 0.5 * np.sin(2 * np.pi * days / 7)
        noise = rng.normal(0, 0.8, size=days_per_user)
        scores = np.clip(baseline + drift * days + weekly + noise, 1, 10)

        for start in range(days_per_user - SEQ_LEN - FORECAST_HORIZON):
            window = scores[start : start + SEQ_LEN]
            future = scores[start + SEQ_LEN : start + SEQ_LEN + FORECAST_HORIZON]

            features = np.zeros((SEQ_LEN, INPUT_SIZE), dtype=np.float32)
            features[:, 0] = window / 10.0  # normalized mood score
            # Other feature slots (sentiment, message_count, emotion/topic one-hots) are left
            # at zero in this synthetic generator — a real Postgres-backed loader would
            # populate them from the messages/mood_logs tables.

            sequences.append(features)
            targets.append(future / 10.0)

    return np.array(sequences), np.array(targets)


class GRUForecaster(nn.Module):
    def __init__(self):
        super().__init__()
        self.rnn = nn.GRU(INPUT_SIZE, 32, num_layers=2, batch_first=True, dropout=0.2)
        self.head = nn.Linear(32, FORECAST_HORIZON)

    def forward(self, x):
        _, h = self.rnn(x)
        return self.head(h[-1])


class LSTMForecaster(nn.Module):
    def __init__(self):
        super().__init__()
        self.rnn = nn.LSTM(INPUT_SIZE, 32, num_layers=2, batch_first=True, dropout=0.2)
        self.head = nn.Linear(32, FORECAST_HORIZON)

    def forward(self, x):
        _, (h, _) = self.rnn(x)
        return self.head(h[-1])


class TransformerForecaster(nn.Module):
    """Small transformer encoder — the natural v2 upgrade once enough longitudinal data
    exists per user (needs more data than GRU/LSTM to avoid overfitting, per the blueprint's
    architecture comparison)."""

    def __init__(self, d_model: int = 32, nhead: int = 4, num_layers: int = 2):
        super().__init__()
        self.input_proj = nn.Linear(INPUT_SIZE, d_model)
        self.pos_embedding = nn.Parameter(torch.zeros(1, SEQ_LEN, d_model))
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True)
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.head = nn.Linear(d_model, FORECAST_HORIZON)

    def forward(self, x):
        x = self.input_proj(x) + self.pos_embedding
        encoded = self.encoder(x)
        pooled = encoded.mean(dim=1)  # mean-pool over the sequence
        return self.head(pooled)


def direction_accuracy(preds: np.ndarray, targets: np.ndarray, last_known: np.ndarray) -> float:
    pred_direction = np.sign(preds[:, -1] - last_known)
    true_direction = np.sign(targets[:, -1] - last_known)
    return float(np.mean(pred_direction == true_direction))


def train_and_eval(model: nn.Module, train_loader, val_loader, epochs: int, lr: float = 1e-3) -> dict:
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    for epoch in range(epochs):
        model.train()
        for x, y in train_loader:
            optimizer.zero_grad()
            pred = model(x)
            loss = loss_fn(pred, y)
            loss.backward()
            optimizer.step()

    model.eval()
    all_preds, all_targets, all_last_known = [], [], []
    with torch.no_grad():
        for x, y in val_loader:
            pred = model(x)
            all_preds.append(pred.numpy())
            all_targets.append(y.numpy())
            all_last_known.append(x[:, -1, 0].numpy())

    preds = np.concatenate(all_preds) * 10  # de-normalize back to 1-10 scale
    targets = np.concatenate(all_targets) * 10
    last_known = np.concatenate(all_last_known) * 10

    mae = float(np.mean(np.abs(preds - targets)))
    rmse = float(np.sqrt(np.mean((preds - targets) ** 2)))
    dir_acc = direction_accuracy(preds, targets, last_known)

    return {"mae": round(mae, 3), "rmse": round(rmse, 3), "direction_accuracy": round(dir_acc, 3)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_source", choices=["synthetic", "postgres"], default="synthetic")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--checkpoint_out", default="./mood_forecaster_gru.pt")
    args = parser.parse_args()

    if args.data_source == "postgres":
        raise NotImplementedError(
            "Wire this up to pull from mood_logs + messages via SYNC_DATABASE_URL once there's "
            "enough real longitudinal data (aim for 60+ days across a meaningful number of users "
            "before this comparison becomes trustworthy)."
        )

    sequences, targets = generate_synthetic_data()
    dataset = MoodSequenceDataset(sequences, targets)
    train_size = int(0.8 * len(dataset))
    train_ds, val_ds = random_split(dataset, [train_size, len(dataset) - train_size])
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    results = {}
    for name, model_cls in [("GRU", GRUForecaster), ("LSTM", LSTMForecaster), ("Transformer", TransformerForecaster)]:
        print(f"\nTraining {name}...")
        model = model_cls()
        metrics = train_and_eval(model, train_loader, val_loader, epochs=args.epochs)
        results[name] = metrics
        print(f"{name} results: {metrics}")
        if name == "GRU":
            torch.save(model.state_dict(), args.checkpoint_out)
            print(f"Saved GRU checkpoint to {args.checkpoint_out} (the current production default).")

    print("\n=== Architecture comparison ===")
    for name, metrics in results.items():
        print(f"{name}: MAE={metrics['mae']}, RMSE={metrics['rmse']}, direction_acc={metrics['direction_accuracy']}")


if __name__ == "__main__":
    main()
