# Zomato Performance Analytics

This project now runs as a full React + FastAPI application by default.

## Architecture
- Frontend: React (Vite + TypeScript) in frontend/
- Backend: FastAPI in backend/
- Data/model source: Python backend reads Zomato Dataset.csv and serves analytics + predictions via REST APIs

## Quick Start (Windows PowerShell)
1) Create and activate a virtual environment (from workspace root)

```powershell
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
```

2) Install backend Python dependencies

```powershell
pip install -r requirements.txt
```

3) Install frontend dependencies

```powershell
Set-Location "frontend"
npm install
Copy-Item ".env.example" ".env" -ErrorAction SilentlyContinue
Set-Location ".."
```

4) Start backend (Terminal 1)

```powershell
Set-Location "backend"
& "../.venv/Scripts/python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

5) Start frontend (Terminal 2)

```powershell
Set-Location "frontend"
npm run dev
```

## URLs
- Frontend: http://127.0.0.1:5173
- Backend docs: http://127.0.0.1:8000/docs
