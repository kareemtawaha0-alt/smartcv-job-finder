# SmartCV Job Finder - CV Analysis & Job Search Platform
A web application that analyzes a CV (resume) and automatically searches for relevant job opportunities based on the extracted insights. Built with FastAPI (Python) + Vite (frontend) and integrates multiple free public job sources (no paid AI required).

## 🚀 Live Demo
Frontend (Netlify): https://YOUR-FRONTEND-URL.netlify.app  
Backend API: https://YOUR-BACKEND-URL

## ✨ Features

### 🧠 CV Analysis (No OpenAI Required)
- Extracts suggested job titles
- Extracts skills
- Estimates experience level
- Generates a short summary
- Works without any API keys by default

### 🔎 Job Search (Step 3) Based on the Analysis
- Automatically searches jobs using the CV analysis result
- Uses free public job APIs:
  - Remotive
  - Remote OK
  - Arbeitnow
- Merges results and removes duplicates
- Optional Adzuna support if you provide your own API keys

### 🎨 Modern UI
- Clean and simple user interface
- Responsive layout
- Loading states and user feedback

## 🧱 Tech Stack
- Backend: Python + FastAPI
- Frontend: Vite + JavaScript
- Job APIs: Remotive, Remote OK, Arbeitnow (+ optional Adzuna)
- No database required

## 📦 Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm

## ⚙️ Quick Start (Local)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

- You can build the frontend with:

```bash
cd frontend
npm run build
```

- Configure CORS origins in `backend/main.py` to match your deployed frontend URL(s).
- 
# Frontend Setup
cd ../frontend
npm install
npm run dev

## 🔗 Environment Configuration
Frontend

Set inside frontend/.env.example (or frontend/.env locally, do not commit it):

VITE_API_BASE_URL=http://127.0.0.1:8000

Backend (Optional)

The backend works without keys.
Optional (Adzuna only):

ADZUNA_APP_ID=
ADZUNA_APP_KEY=

## 📁 Project Structure
smartcv-job-finder
/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    ├── package.json
    └── .env.example

## 🎯 How It Works

User submits CV text.

Backend analyzes the CV and extracts job titles, skills and experience level.

Backend builds keywords from the analysis.

Backend searches jobs from Remotive, Remote OK and Arbeitnow.

Results are merged and returned to the frontend.


**Built with ❤️ for professional, trustworthy agreements**

    

