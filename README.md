# GridGuard

A web application for municipal staff to detect and respond to illegal electricity connections and infrastructure tampering in real time.

## The problem

According to Eskom, South Africa loses an estimated R30 billion a year to illegal electricity connections and related criminal activity — one of the largest contributors to loadshedding. Loadshedding in turn drives up crime in vulnerable communities, particularly cable theft. Municipalities generally don't have the resources to proactively detect and respond to this in real time.

## The solution

GridGuard combines two detection mechanisms behind a single staff dashboard:

1. **Usage-pattern risk scoring** — a machine learning model analyses each household's prepaid electricity purchase-to-consumption ratio over time and flags patterns consistent with illegal connections (e.g. usage climbing while purchases stop).
2. **Infrastructure tamper detection** — motion sensors installed along critical electrical infrastructure detect unusual cable movement. When tampering is suspected, the system automatically creates an alert and dispatches notifications.

Both detection paths feed into the same alerts pipeline, giving municipal staff a live dashboard showing at-risk households, open alerts, and a real-time sensor feed.

## Why synthetic data and a simulated sensor feed

This project doesn't have access to real Eskom or municipal prepaid electricity data, and there's no physical IoT hardware installed anywhere. Rather than pretend otherwise, GridGuard is explicit about this:

- **Purchase/consumption data** is generated synthetically (`ml_training/generate_synthetic_data.py`), modelling realistic household electricity patterns with an injected "tampering" behaviour (usage keeps climbing while purchases drop off) used to train the risk model.
- **Sensor readings** are simulated by a background process (`app/sensor_simulator.py`) that emits normal/tamper events on a timer, exercising the exact same alert → notification pipeline that real sensor hardware would trigger.

This is a demonstrated proof-of-concept of the detection *system*, not a production deployment on real data — the architecture is built so that swapping in a real data source or real sensor hardware wouldn't require changing the alerting, scoring, or dashboard logic.

## Tech stack

**Backend:** Python, FastAPI, SQLAlchemy (SQLite locally, Postgres-ready), JWT auth (python-jose + passlib), WebSockets, scikit-learn, joblib, SMTP (email) and Twilio (SMS) for alert dispatch

**Frontend:** HTML, CSS, vanilla JavaScript (no framework), Chart.js for the consumption chart

**ML:** RandomForestClassifier trained on synthetic household data, engineered features (purchase-to-consumption ratio, rolling averages, trend)

## Features

- Municipal staff authentication (register/login, JWT-secured API)
- Household management — add households, log monthly purchase/consumption records
- Automatic risk scoring on every logged consumption record, with alerts fired above a threshold
- Live simulated sensor feed over WebSocket, with tamper events automatically creating alerts
- Alerts page with Open/Resolved/All filtering and one-click resolve
- Email/SMS alert dispatch (SMTP + Twilio), gracefully no-ops in "demo mode" without credentials configured
- Client-side household search (by address, meter number, or ward)
- Purchase-vs-consumption chart per household

## Project structure
