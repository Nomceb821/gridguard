"""
Trains a risk-scoring model on the synthetic household dataset and saves it
for the FastAPI backend to load.

We use a supervised RandomForestClassifier here rather than pure unsupervised
anomaly detection because the synthetic data gives us ground-truth labels
(is_tampered), which lets us report real precision/recall numbers -- useful
to quote in an interview. In production, with real data, labels would come
from confirmed inspections, and you'd likely start unsupervised (Isolation
Forest) until enough confirmed cases existed to retrain supervised.

Run:
    python generate_synthetic_data.py
    python train_model.py
"""

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

FEATURES = [
    "purchase_rand",
    "consumption_kwh",
    "ratio",
    "consumption_3m_avg",
    "purchase_3m_avg",
    "consumption_trend",
    "ratio_trend",
]
TARGET = "is_tampered"


def main():
    df = pd.read_csv("synthetic_households.csv")

    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        class_weight="balanced",  # tampering is a minority class
        random_state=42,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]

    print(classification_report(y_test, preds, target_names=["normal", "tampered"]))
    print(f"ROC AUC: {roc_auc_score(y_test, probs):.3f}")

    joblib.dump({"model": model, "features": FEATURES}, "risk_model.pkl")
    print("Saved model to risk_model.pkl")


if __name__ == "__main__":
    main()