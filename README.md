# Zomato Performance Analytics Dashboard

A React + FastAPI dashboard for exploring Zomato delivery performance, rider efficiency, demand patterns, external factors, location intelligence, and delivery-time prediction.

## Project Layout
- `frontend/`: Vite + React + TypeScript dashboard UI
- `backend/`: FastAPI service that loads and analyzes `Zomato Dataset.csv`
- `Zomato Dataset.csv`: dataset used by the backend for analytics and prediction models

## What The App Does
- Executive overview KPIs and order trends
- Delivery operations analysis by city, weather, traffic, vehicle, and order type
- Rider efficiency scoring and ranking
- Demand and time-of-day analysis
- External impact analysis for weather, traffic, festival, and vehicle condition
- Location intelligence with map-oriented summaries
- Predictive analytics for delivery time and delay probability

## Backend API
The backend exposes these routes:
- `GET /api/health`
- `GET /api/filters/options`
- `POST /api/filters/apply`
- `POST /api/executive-overview`
- `POST /api/delivery-operations`
- `POST /api/rider-efficiency`
- `POST /api/demand-time`
- `POST /api/external-impact`
- `POST /api/location-intelligence`
- `POST /api/predictive-assets`
- `POST /api/predict`

## How To Run The Backend
From the repository root in Windows PowerShell:

```powershell
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
pip install -r backend/requirements.txt
Set-Location "backend"
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

If you already have the virtual environment created and activated, the only commands you need are:

```powershell
Set-Location "backend"
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## How To Run The Frontend
In a second terminal:

```powershell
Set-Location "frontend"
npm install
npm run dev
```

## URLs
- Frontend: http://127.0.0.1:5173
- Backend API docs: http://127.0.0.1:8000/docs

## Configuration Notes
- The frontend defaults to `http://127.0.0.1:8000` for API calls.
- You can override the frontend API base URL with `VITE_API_BASE_URL`.
- The backend reads `Zomato Dataset.csv` from the repository root.
