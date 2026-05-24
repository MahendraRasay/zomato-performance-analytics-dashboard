React Frontend + FastAPI Backend Setup

What was added
- backend/main.py: FastAPI server and full analytics/prediction API endpoints.
- backend/core.py: data prep, filtering, page payloads, and model logic extracted from Streamlit flow.
- backend/schemas.py: request models.
- backend/requirements.txt: backend dependencies.
- frontend/: React + TypeScript app scaffold.
- frontend/src/App.tsx: full migrated multi-page React dashboard wired to API.
- frontend/src/api.ts: centralized API client (supports VITE_API_BASE_URL).

Current API endpoints
- GET /api/health
- GET /api/filters/options
- POST /api/filters/apply
- POST /api/executive-overview
- POST /api/delivery-operations
- POST /api/rider-efficiency
- POST /api/demand-time
- POST /api/external-impact
- POST /api/location-intelligence
- POST /api/predictive-assets
- POST /api/predict

Frontend pages now backed by API
- Executive Overview
- Delivery Operations
- Rider Efficiency
- Demand & Time Analysis
- External Impact Analysis
- Predictive Analytics
- Location Intelligence

Run backend
1) Open terminal in workspace root.
2) Run:
   Set-Location "backend"
   & "../.venv/Scripts/python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

Run frontend
1) Open another terminal in workspace root.
2) Run:
   Set-Location "frontend"
   Copy-Item ".env.example" ".env" -ErrorAction SilentlyContinue
   npm run dev

Open app
- Frontend: http://localhost:5173
- Backend docs: http://127.0.0.1:8000/docs

Notes
- Frontend is fully React and reads all dashboard/prediction data from the Python backend APIs.
