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
gridguard/
├── backend/
│ ├── app/
│ │ ├── main.py # FastAPI app entrypoint
│ │ ├── config.py # Settings loaded from .env
│ │ ├── database.py # SQLAlchemy engine/session
│ │ ├── models.py # User, Household, ConsumptionRecord, Alert
│ │ ├── schemas.py # Pydantic request/response models
│ │ ├── auth.py # JWT auth, password hashing
│ │ ├── ml_model.py # Loads trained model, scores risk
│ │ ├── alerts_service.py # Email/SMS dispatch
│ │ ├── sensor_simulator.py # Simulated sensor feed + WebSocket manager
│ │ └── routers/
│ │ ├── auth.py
│ │ ├── households.py
│ │ ├── alerts.py
│ │ └── sensors.py
│ ├── ml_training/
│ │ ├── generate_synthetic_data.py
│ │ └── train_model.py
│ ├── requirements.txt
│ └── .env.example
└── frontend/
├── index.html # Login / register
├── dashboard.html # Overview: households + chart
├── alerts.html # Alerts, with filtering
├── sensors.html # Live sensor feed
├── style.css
├── script.js
└── config.js # Points frontend at the backend URL

## Running it locally

### Backend

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash; use venv/bin/activate on Mac/Linux
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set a real `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Generate the synthetic data and train the model:
```bash
cd ml_training
python generate_synthetic_data.py
python train_model.py
cd ..
```

Run the API:
```bash
uvicorn app.main:app --reload
```
The API is now live at `http://localhost:8000` (interactive docs at `/docs`).

### Frontend

Serve the `frontend/` folder with a local server (e.g. VS Code's Live Server extension) rather than opening the HTML files directly — the backend's CORS settings and the browser's handling of `file://` origins don't play well together otherwise.

Update `frontend/config.js` if your backend isn't running on `localhost:8000`.

## Model performance

The trained model reports perfect precision/recall on the synthetic test set. This is expected, not a sign of a magic model — the synthetic data has a clean, deterministic rule for what "tampering" looks like. With real municipal data, performance would be meaningfully noisier, and the model would need retraining against confirmed real-world inspection outcomes.

## Limitations & future work

- Replace synthetic data with real (anonymised) prepaid electricity purchase data, if/when access is available
- Replace the simulated sensor feed with real IoT hardware readings
- Move from a supervised model (which relies on clean synthetic labels) to an unsupervised anomaly detection approach (e.g. Isolation Forest) as a starting point on real, unlabeled data, retraining supervised once enough confirmed cases exist
- Move from SQLite to Postgres for production use
- Deploy the backend (Render/Railway) and frontend (GitHub Pages) for a live public demo

## Author

Nomcebo Nkomo — Software Developer & Data Scientist
[GitHub](https://github.com/Nomceb821) · [LinkedIn](https://www.linkedin.com/in/nomcebonkomo3/)
