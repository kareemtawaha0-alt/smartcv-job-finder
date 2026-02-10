# SmartCV Job Finder

SmartCV Job Finder is a full-stack web application that lets users upload their CV, analyze their skills using OpenAI, and search for matching jobs from online job boards.

## Project Structure

- `frontend/` – React + Vite + TailwindCSS single-page app
- `backend/` – FastAPI backend with CV parsing, AI analysis, and job search
- `sample_cvs/` – Example CVs for testing

## Prerequisites

- Node.js (LTS recommended)
- Python 3.10+
- An OpenAI API key
- (Optional but recommended) Adzuna job search API credentials

---

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file in `backend/` based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and fill in:

- `HF_TOKEN (optional): Hugging Face token. If omitted, rule-based fallback is used.
- Optional Adzuna settings for live job search:
  - `ADZUNA_APP_ID`
  - `ADZUNA_APP_KEY`
  - `ADZUNA_COUNTRY` (e.g. `gb`, `us`, `ae`)
  - `DEFAULT_JOB_LOCATION` (fallback location, e.g. `Remote`)

Run the backend:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The FastAPI docs will be available at: `http://localhost:8000/docs`.

---

## Frontend Setup

```bash
cd frontend
npm install
```

Create a `.env` file in `frontend/` based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and set:

```bash
VITE_API_BASE_URL="http://localhost:8000"
```

Run the development server:

```bash
npm run dev
```

The app will be available (by default) at `http://localhost:5173`.

---

## Flow

1. Upload a CV (PDF or DOCX, simple text also supported).
2. The backend:
   - Extracts text.
   - Calls OpenAI to analyze job titles, skills, experience, and recommended job types.
   - Uses that to query the Adzuna jobs API (if configured) and returns matching jobs.
   - Falls back to mocked job results if no external job API is configured.
3. The frontend displays a modern results table with:
   - Job Title
   - Company
   - Location
   - Short description
   - Link to apply

The system **never** auto-applies; it only shows links.

---

## Production Notes

- You can deploy the backend to any Python-friendly host (e.g. Docker, cloud VM, etc.).
- You can build the frontend with:

```bash
cd frontend
npm run build
```

- Configure CORS origins in `backend/main.py` to match your deployed frontend URL(s).

