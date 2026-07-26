"""
Loads the RandomForest risk model trained in ml_training/train_model.py and
scores new consumption records against it.

If risk_model.pkl hasn't been generated yet (e.g. fresh clone before running
the training scripts), predict_risk() falls back to a simple rule-based
score so the API still functions for a demo.
"""

import logging
import os

import joblib

logger = logging.getLogger("gridguard.ml")

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml_training", "risk_model.pkl")

_model_bundle = None


def _load_model():
    global _model_bundle
    if _model_bundle is None:
        if os.path.exists(MODEL_PATH):
            _model_bundle = joblib.load(MODEL_PATH)
            logger.info("Loaded trained risk model from %s", MODEL_PATH)
        else:
            _model_bundle = None
            logger.warning("No trained model found at %s — using fallback rule-based scoring", MODEL_PATH)
    return _model_bundle


def _fallback_score(purchase_rand: float, consumption_kwh: float) -> float:
    """Simple heuristic used only if no trained model is present: a low
    purchase-to-consumption ratio is suspicious."""
    ratio = purchase_rand / max(consumption_kwh, 1)
    if ratio < 0.3:
        return min(0.5 + (0.3 - ratio), 0.95)
    return max(0.1, 0.5 - ratio * 0.3)


def predict_risk(features: dict) -> float:
    """
    features expects: purchase_rand, consumption_kwh, ratio,
    consumption_3m_avg, purchase_3m_avg, consumption_trend, ratio_trend
    Returns a probability-like score between 0 and 1.
    """
    bundle = _load_model()
    if bundle is None:
        return round(_fallback_score(features["purchase_rand"], features["consumption_kwh"]), 3)

    model = bundle["model"]
    feature_order = bundle["features"]
    row = [[features.get(f, 0) for f in feature_order]]
    proba = model.predict_proba(row)[0][1]
    return round(float(proba), 3)