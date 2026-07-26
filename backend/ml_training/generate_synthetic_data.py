"""
Generates a synthetic dataset of prepaid electricity purchase and consumption
patterns for municipal households, standing in for real Eskom/municipal data
that isn't publicly accessible for a portfolio project.

Two household classes are simulated:
  - "normal":   purchases roughly track consumption over time
  - "tampered": consumption keeps rising while purchases stop or shrink
                (the pattern illegal connections/meter tampering produces)

Output: backend/ml_training/synthetic_households.csv
Each row = one household-month record with engineered features used by
train_model.py.
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

N_HOUSEHOLDS = 1200
MONTHS = 12
TAMPER_RATE = 0.12  # share of households that show tampering behaviour


def simulate_household(household_id: int, tampered: bool) -> pd.DataFrame:
    base_consumption = RNG.normal(180, 40)  # kWh/month baseline
    base_consumption = max(base_consumption, 60)

    rows = []
    purchase_credit = RNG.normal(200, 50)  # starting credit in Rand
    tamper_start = RNG.integers(3, MONTHS - 2) if tampered else None

    for month in range(MONTHS):
        seasonal = 1 + 0.15 * np.sin((month / 12) * 2 * np.pi)  # winter bump
        consumption = base_consumption * seasonal + RNG.normal(0, 15)
        consumption = max(consumption, 20)

        if tampered and month >= tamper_start:
            months_since = month - tamper_start
            consumption *= 1 + 0.18 * months_since  # usage climbs
            purchase = max(RNG.normal(20, 15), 0) * max(1 - 0.15 * months_since, 0.05)
        else:
            purchase = consumption * RNG.normal(1.05, 0.15)
            purchase = max(purchase, 0)

        rows.append({
            "household_id": household_id,
            "month": month,
            "purchase_rand": round(purchase, 2),
            "consumption_kwh": round(consumption, 2),
            "is_tampered": int(tampered and month >= tamper_start),
        })

    return pd.DataFrame(rows)


def build_dataset() -> pd.DataFrame:
    n_tampered = int(N_HOUSEHOLDS * TAMPER_RATE)
    tampered_flags = [True] * n_tampered + [False] * (N_HOUSEHOLDS - n_tampered)
    RNG.shuffle(tampered_flags)

    frames = [
        simulate_household(hid, tampered_flags[hid])
        for hid in range(N_HOUSEHOLDS)
    ]
    return pd.concat(frames, ignore_index=True)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Rolling features a model can actually learn from: recent trend and
    the purchase-to-consumption ratio, which is the core tell for tampering."""
    df = df.sort_values(["household_id", "month"]).copy()
    df["ratio"] = df["purchase_rand"] / df["consumption_kwh"].clip(lower=1)

    df["consumption_3m_avg"] = (
        df.groupby("household_id")["consumption_kwh"]
        .transform(lambda s: s.rolling(3, min_periods=1).mean())
    )
    df["purchase_3m_avg"] = (
        df.groupby("household_id")["purchase_rand"]
        .transform(lambda s: s.rolling(3, min_periods=1).mean())
    )
    df["consumption_trend"] = (
        df.groupby("household_id")["consumption_kwh"]
        .transform(lambda s: s.diff().rolling(3, min_periods=1).mean())
        .fillna(0)
    )
    df["ratio_trend"] = (
        df.groupby("household_id")["ratio"]
        .transform(lambda s: s.diff().rolling(3, min_periods=1).mean())
        .fillna(0)
    )
    return df


if __name__ == "__main__":
    data = build_dataset()
    data = add_features(data)
    out_path = "synthetic_households.csv"
    data.to_csv(out_path, index=False)
    print(f"Wrote {len(data)} rows for {N_HOUSEHOLDS} households to {out_path}")
    print(f"Tampered rows: {data['is_tampered'].sum()} ({data['is_tampered'].mean():.1%})")