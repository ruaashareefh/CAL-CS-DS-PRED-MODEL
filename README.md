# Berkeley Course Difficulty Predictor

Predicts average GPA for UC Berkeley CS and Data Science courses using
historical grade distributions from BerkeleyTime.

Ridge Regression ended up outperforming Random Forest here (R²: 0.916 vs
0.308) — the dataset is small (30 courses), so the simpler model generalizes
better. Both are served via a FastAPI backend with a React frontend.

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

---

## Models

| Model | Features | MAE | R² | Coverage |
|---|---|---|---|---|
| Ridge Regression | grade entropy, skewness, % A-range, % passing | 0.041 | 0.916 | All 30 courses |
| Random Forest (100 trees, depth=3) | 11 features incl. grading structure | 0.061 | 0.308 | 8 courses |

All predictions include 95% confidence intervals.

---

## Quick Start

**Requirements:** Python 3.11, Node.js 18+
```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000 (Swagger docs at /docs)

# Frontend
cd frontend
npm install && npm run dev
# → http://localhost:5173
```

**Or with Docker:**
```bash
cd deployment && docker-compose up --build
# → http://localhost:8000
```

---

## API

Base URL: `http://localhost:8000/api/v1`

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | DB + model status |
| `/courses` | GET | All courses (filterable by subject) |
| `/courses/{id}` | GET | Course details + grade distribution |
| `/predict` | POST | Predict GPA for a course |
| `/predict/batch` | POST | Batch predictions |
| `/models` | GET | Model metrics |

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"course_id": 1, "model_type": "grade_distribution"}'
```
```json
{
  "prediction": {
    "predicted_gpa": 3.38,
    "actual_gpa": 3.39,
    "confidence_interval": { "lower": 3.30, "upper": 3.46 }
  },
  "model_info": {
    "model_name": "Ridge Regression",
    "mae": 0.041,
    "r2": 0.916
  }
}
```

---

## Project Structure
```
├── backend/
│   └── app/
│       ├── main.py         # Entry point
│       ├── models/         # ML loading + schemas
│       ├── database/       # SQLite queries
│       └── routers/        # Endpoints
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       └── services/       # API client
├── data/courses.db
├── models/
│   ├── model_grade_distribution.pkl
│   └── model_full.pkl
├── scripts/                # Data pipeline
└── deployment/             # Docker + Render config
```

---

## Data Pipeline
```bash
python scripts/fetch_berkeleytime_grades.py  # pull from BerkeleyTime API
python scripts/init_database.py
python scripts/engineer_features.py
python scripts/train_model.py
python scripts/visualize_features.py
```

---

## Environment Variables
```env
ENVIRONMENT=development
DB_PATH=data/courses.db
CORS_ORIGINS=["http://localhost:5173"]
LOG_LEVEL=INFO
```

---

## Deployment (Render.com)
```bash
git push origin main
```
Connect repo on Render → it auto-detects `render.yaml`. Set `CORS_ORIGINS`
to your app URL. Build takes ~5 minutes.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `No module named 'fastapi'` | `pip install -r backend/requirements.txt` |
| `Database not found` | Check `data/courses.db` exists |
| Python 3.13 issues | Switch to 3.11 (`pyenv local 3.11`) |
| `Cannot find module 'react'` | `cd frontend && npm install` |
| CORS errors | Add frontend URL to `CORS_ORIGINS` in `backend/app/config.py` |

---

## What's Next

- Expand beyond 30 courses
- Collect grading structure for all courses (unlocks the RF model more broadly)
- Professor-level predictions
- Real-time sync with BerkeleyTime

---

Data: [BerkeleyTime](https://berkeleytime.com) | Stack: FastAPI + React + scikit-learn
