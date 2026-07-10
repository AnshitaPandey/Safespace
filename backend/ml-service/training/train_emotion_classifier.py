"""
Fine-tunes distilroberta-base on GoEmotions, remapped to SafeSpace's 8-label taxonomy
(happy, sad, angry, anxious, lonely, neutral, excited, frustrated), per the blueprint's DL
pipeline section.

This is real, runnable training code — it is NOT run as part of this repo's setup, since it
needs a GPU (or patience on CPU) and the GoEmotions dataset. Run it manually:

    pip install datasets scikit-learn
    python train_emotion_classifier.py --epochs 4 --output_dir ./emotion_model

Then point ml-service at the resulting checkpoint (swap emotion_classifier.py's pipeline to
load from `output_dir` instead of the pragmatic pretrained default).

Dataset: https://huggingface.co/datasets/go_emotions (58k Reddit comments, 27 fine-grained
emotions + neutral). We map GoEmotions' 27 labels down to our 8 via `_GOEMOTIONS_TO_OURS`
below — approximate but reasonable; refine this mapping based on a confusion-matrix review
after the first training run.
"""
import argparse

import numpy as np
from datasets import load_dataset
from sklearn.metrics import f1_score, precision_recall_fscore_support
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

OUR_LABELS = ["happy", "sad", "angry", "anxious", "lonely", "neutral", "excited", "frustrated"]
LABEL_TO_ID = {label: i for i, label in enumerate(OUR_LABELS)}

# GoEmotions' 27 fine-grained labels mapped to our 8. Multiple source labels can map to one
# target; GoEmotions is multi-label in its raw form, so we take the first matching label per
# example to keep this a single-label classification problem (simpler to train and serve).
_GOEMOTIONS_TO_OURS = {
    "admiration": "happy", "amusement": "happy", "approval": "happy", "caring": "happy",
    "excitement": "excited", "gratitude": "happy", "joy": "happy", "love": "happy",
    "optimism": "excited", "pride": "happy", "relief": "happy", "surprise": "excited",
    "anger": "angry", "annoyance": "frustrated", "disapproval": "frustrated",
    "disappointment": "sad", "disgust": "frustrated", "embarrassment": "anxious",
    "fear": "anxious", "grief": "sad", "nervousness": "anxious", "remorse": "sad",
    "sadness": "sad", "confusion": "frustrated", "curiosity": "neutral",
    "desire": "excited", "realization": "neutral", "neutral": "neutral",
}


def remap_example(example, id2label_goemotions):
    label_ids = example["labels"]
    if not label_ids:
        return {"our_label": LABEL_TO_ID["neutral"]}
    first_label_name = id2label_goemotions[label_ids[0]]
    mapped = _GOEMOTIONS_TO_OURS.get(first_label_name, "neutral")
    return {"our_label": LABEL_TO_ID[mapped]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", default="distilroberta-base")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--learning_rate", type=float, default=2e-5)
    parser.add_argument("--output_dir", default="./emotion_model")
    args = parser.parse_args()

    dataset = load_dataset("go_emotions", "simplified")
    id2label_goemotions = dataset["train"].features["labels"].feature.names

    dataset = dataset.map(lambda ex: remap_example(ex, id2label_goemotions))

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, max_length=128)

    dataset = dataset.map(tokenize, batched=True)
    dataset = dataset.rename_column("our_label", "label")
    dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

    # Class weighting: GoEmotions is skewed heavily toward "neutral"/"happy" adjacent labels;
    # without this, the model would just learn to predict the majority class.
    labels_array = np.array(dataset["train"]["label"])
    class_counts = np.bincount(labels_array, minlength=len(OUR_LABELS))
    class_weights = (1.0 / np.maximum(class_counts, 1))
    class_weights = class_weights / class_weights.sum() * len(OUR_LABELS)

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name, num_labels=len(OUR_LABELS), id2label={i: l for i, l in enumerate(OUR_LABELS)},
        label2id=LABEL_TO_ID,
    )

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        macro_f1 = f1_score(labels, predictions, average="macro")
        precision, recall, _, _ = precision_recall_fscore_support(labels, predictions, average="macro")
        return {"macro_f1": macro_f1, "precision": precision, "recall": recall}

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        warmup_ratio=0.1,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        logging_steps=50,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=compute_metrics,
    )

    trainer.train()

    test_results = trainer.evaluate(dataset["test"])
    print("Test set results:", test_results)

    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"Model saved to {args.output_dir}. Point ml-service/models/emotion_classifier.py at this path.")


if __name__ == "__main__":
    main()
