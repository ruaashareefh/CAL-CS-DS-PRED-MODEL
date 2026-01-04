# UC Berkeley Course Difficulty Predictor

A full-stack web application that predicts course difficulty (average GPA) using machine learning models trained on historical grade distribution data from UC Berkeley.

![Tech Stack](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

## Features

- **GPA Prediction**: Predict course average GPA with ±0.04 accuracy
- **Two ML Models**:
  - Ridge Regression (MAE: 0.041, R²: 0.916) - Works for all 30 courses
  - Random Forest (MAE: 0.061, R²: 0.308) - Requires grading structure data
- **Interactive UI**: Search courses, visualize predictions, browse course catalog
- **Confidence Intervals**: 95% confidence intervals for all predictions
- **Auto-generated API Docs**: Swagger UI at `/docs`

## Dataset

- **30 courses** from UC Berkeley (COMPSCI and DATA)
- **8 courses** with detailed grading structure data
- **Data source**: BerkleyTime API
- **Features**: Grade entropy, skewness, % A-range, grading percentages

## Quick Start

### Prerequisites

- Python 3.11 (backend)
- Node.js 18+ (frontend)
- npm or yarn

### Option 1: Run Locally (Development)

#### Backend (FastAPI)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload

# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

#### Frontend (React + Vite)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Frontend available at http://localhost:5173
```

### Option 2: Docker (Production Build)

```bash
# Build and run with Docker Compose
cd deployment
docker-compose up --build

# Application available at http://localhost:8000
```

### Option 3: Production Build

```bash
# Build frontend
cd frontend
npm run build

# Serve with FastAPI
cd ..
ENVIRONMENT=production uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Application at http://localhost:8000
```

## API Endpoints

Base URL: `http://localhost:8000/api/v1`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (DB connected, models loaded) |
| `/courses` | GET | List all courses (supports filtering by subject) |
| `/courses/{id}` | GET | Get course details with grade distribution |
| `/predict` | POST | Predict GPA for a course |
| `/predict/batch` | POST | Batch predictions for multiple courses |
| `/models` | GET | List available ML models with metrics |
| `/static/plots/{filename}` | GET | Serve visualization plots |

### Example: Predict GPA

```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": 1,
    "model_type": "grade_distribution"
  }'
```

Response:
```json
{
  "prediction": {
    "predicted_gpa": 3.38,
    "actual_gpa": 3.39,
    "error": -0.01,
    "confidence_interval": {
      "lower": 3.30,
      "upper": 3.46
    }
  },
  "model_info": {
    "model_name": "Ridge Regression",
    "mae": 0.041,
    "r2": 0.916,
    "features_used": ["grade_entropy", "grade_skewness", "pct_a_range", "pct_passing"]
  }
}
```

## Project Structure

```
CAL-CS-DS-PRED-MODEL/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py         # App entry point
│   │   ├── config.py       # Settings
│   │   ├── models/         # ML model loading & schemas
│   │   ├── database/       # SQLite queries
│   │   └── routers/        # API endpoints
│   └── requirements.txt
│
├── frontend/               # React application
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API client
│   │   └── styles/        # CSS
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   └── courses.db         # SQLite database
│
├── models/                # Trained ML models
│   ├── model_grade_distribution.pkl
│   └── model_full.pkl
│
├── plots/                 # Visualizations
│
├── deployment/            # Docker configs
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── render.yaml
│
└── scripts/              # Data pipeline scripts
```

## Tech Stack

### Backend
- **FastAPI** - Modern async web framework
- **Pydantic** - Data validation
- **scikit-learn** - ML models (Ridge, RandomForest)
- **SQLite** - Database
- **Uvicorn** - ASGI server

### Frontend
- **React 18** - UI library
- **Vite** - Build tool
- **React Query** - Server state management
- **Axios** - HTTP client
- **React Router** - Navigation

### Deployment
- **Docker** - Containerization
- **Render.com** - Cloud platform (or Heroku, AWS, etc.)

## ML Models

### Model 1: Grade Distribution Only
- **Type**: Ridge Regression
- **Features**: grade_entropy, grade_skewness, pct_a_range, pct_passing
- **Performance**: MAE=0.041, RMSE=0.060, R²=0.916
- **Coverage**: All 30 courses

### Model 2: Full Features
- **Type**: Random Forest (100 trees, max_depth=3)
- **Features**: 11 features including grading structure
- **Performance**: MAE=0.061, RMSE=0.069, R²=0.308
- **Coverage**: 8 courses with grading structure data

## Deployment

### Deploy to Render.com

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Connect to Render**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`

3. **Configure Environment Variables**
   - Set `CORS_ORIGINS` to `["https://your-app.onrender.com"]`

4. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete (~5 minutes)
   - Access at `https://your-app.onrender.com`

### Deploy with Docker

```bash
# Build image
docker build -t cal-course-predictor -f deployment/Dockerfile .

# Run container
docker run -p 8000:8000 cal-course-predictor
```

## Development

### Backend Development

```bash
cd backend

# Install dev dependencies
pip install pytest httpx

# Run tests (if you create them)
pytest tests/

# Format code
black app/

# Type checking
mypy app/
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Testing the Application

### Test Backend API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Get all courses
curl http://localhost:8000/api/v1/courses

# Get specific course
curl http://localhost:8000/api/v1/courses/1

# Predict GPA
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"course_id": 1, "model_type": "grade_distribution"}'

# View API docs
open http://localhost:8000/docs
```

### Test Frontend

1. Open http://localhost:5173
2. Search for a course (e.g., "COMPSCI 61A")
3. Select model type
4. Click "Predict GPA"
5. View prediction results with confidence interval

## Data Pipeline

The original data pipeline scripts are in `scripts/`:

```bash
# Fetch grade data from BerkleyTime API
python scripts/fetch_berkeleytime_grades.py

# Initialize database
python scripts/init_database.py

# Engineer features
python scripts/engineer_features.py

# Train models
python scripts/train_model.py

# Generate visualizations
python scripts/visualize_features.py
```

## Environment Variables

Create a `.env` file in the root directory:

```env
ENVIRONMENT=development
DB_PATH=data/courses.db
CORS_ORIGINS=["http://localhost:5173"]
LOG_LEVEL=INFO
```

## Troubleshooting

### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`
```bash
pip install -r backend/requirements.txt
```

**Problem**: `Database not found`
```bash
# Ensure data/courses.db exists
ls data/courses.db
```

**Problem**: Python 3.13 compatibility issues
```bash
# Use Python 3.11 instead
pyenv install 3.11
pyenv local 3.11
```

### Frontend Issues

**Problem**: `Cannot find module 'react'`
```bash
cd frontend
npm install
```

**Problem**: CORS errors
```bash
# Make sure backend CORS_ORIGINS includes frontend URL
# Check backend/app/config.py
```

## Performance

- **Backend**: ~10ms per prediction
- **Frontend**: First Contentful Paint < 1.5s
- **Database**: 30 courses, <1MB
- **Models**: Total size ~100KB

## Future Enhancements

- [ ] Add more courses (expand beyond 30)
- [ ] Collect grading structure for all courses
- [ ] Implement model retraining pipeline
- [ ] Add professor-specific predictions
- [ ] User authentication and favorites
- [ ] Mobile app (React Native)
- [ ] Real-time data updates from BerkleyTime
- [ ] A/B testing for model improvements
- [ ] Add course prerequisites graph

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is for educational purposes.

## Acknowledgments

- Data source: [BerkleyTime](https://berkeleytime.com)
- UC Berkeley for course data
- FastAPI and React communities

## Contact

For questions or feedback, please open an issue on GitHub.

---

**Built with FastAPI + React | ML Powered | UC Berkeley Data**
