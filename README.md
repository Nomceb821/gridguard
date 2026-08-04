# GridGuard

A web application for municipal staff to detect and respond to illegal electricity connections and infrastructure tampering in real time.

**Live demo:** https://nomceb821.github.io/gridguard/
**Live API docs:** https://gridguard-api.onrender.com/docs

> Note: the backend runs on Render's free tier, which spins down after ~15 minutes of inactivity. The first request after a quiet period can take 30–60 seconds to respond while it wakes back up — that's expected, not a bug.

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

**Backend:** Python, FastAPI, SQLAlchemy, JWT auth (python-jose + passlib), WebSockets, scikit-learn, joblib, SMTP (email) and Twilio (SMS) for alert dispatch

**Frontend:** HTML, CSS, vanilla JavaScript (no framework), Chart.js for the consumption chart

**ML:** RandomForestClassifier trained on synthetic household data, engineered features (purchase-to-consumption ratio, rolling averages, trend)

**Deployment:** Backend on Render (Postgres database + web service), frontend on GitHub Pages

## Features

- Municipal staff authentication (register/login, JWT-secured API)
- Household management — add households, log monthly purchase/consumption records
- Automatic risk scoring on every logged consumption record, with alerts fired above a threshold
- Live simulated sensor feed over WebSocket, with tamper events automatically creating alerts
- Alerts page with Open/Resolved/All filtering and one-click resolve
- Email/SMS alert dispatch (SMTP + Twilio), gracefully no-ops in "demo mode" without credentials configured
- Client-side household search (by address, meter number, or ward)
- Purchase-vs-consumption chart per household

**Project Structure**

<img width="653" height="505" alt="image" src="https://github.com/user-attachments/assets/6605e420-d5b1-467f-a4b1-700bfdb15165" />




## Running it locally

### Backend

bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash; use venv/bin/activate on Mac/Linux
pip install -r requirements.txt

Copy `.env.example` to `.env` and set a real `SECRET_KEY`:

bash
python -c "import secrets; print(secrets.token_hex(32))"

Locally, `DATABASE_URL` defaults to SQLite (`sqlite:///./gridguard.db`) — no separate database setup needed for local development.

Generate the synthetic data and train the model:
bash
cd ml_training
python generate_synthetic_data.py
python train_model.py
cd ..


Run the API:
bash
uvicorn app.main:app --reload

The API is now live at `http://localhost:8000` (interactive docs at `/docs`).

### Frontend

Serve the `docs/` folder with a local server (e.g. VS Code's Live Server extension) rather than opening the HTML files directly — the backend's CORS settings and the browser's handling of `file://` origins don't play well together otherwise.

Update `docs/config.js` to point at `http://localhost:8000` for local development (the live version points at the deployed Render URL instead).

## Deployment

- **Backend:** deployed on Render as a Python web service, with a managed Render PostgreSQL database. The build step regenerates the synthetic dataset and retrains the model on every deploy, since those files aren't committed to the repo.
- **Frontend:** deployed via GitHub Pages, serving directly from the `docs/` folder on the `main` branch (GitHub Pages only supports `/root` or `/docs` as a source folder, hence the naming).
- Environment variables (`SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`) are configured directly in Render's dashboard and are never committed to the repo.

## Model performance

The trained model reports perfect precision/recall on the synthetic test set. This is expected, not a sign of a magic model — the synthetic data has a clean, deterministic rule for what "tampering" looks like. With real municipal data, performance would be meaningfully noisier, and the model would need retraining against confirmed real-world inspection outcomes.

## Limitations & future work

- Replace synthetic data with real (anonymised) prepaid electricity purchase data, if/when access is available
- Replace the simulated sensor feed with real IoT hardware readings
- Move from a supervised model (which relies on clean synthetic labels) to an unsupervised anomaly detection approach (e.g. Isolation Forest) as a starting point on real, unlabeled data, retraining supervised once enough confirmed cases exist
- Add automated tests
- Custom domain / paid Render tier to avoid free-tier cold starts

## Author

Nomcebo Nkomo — Software Developer & Data Scientist
[GitHub](https://github.com/Nomceb821) · [LinkedIn](https://www.linkedin.com/in/nomcebonkomo3/)
- Top-nav multi-page layout (Overview / Alerts / Sensors) with a live connection indicator

