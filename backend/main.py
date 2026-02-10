import os
import re
from typing import List, Optional, Any, Dict
from urllib.parse import quote_plus

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import pdfplumber
from docx import Document
import requests

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")  # optional
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "gb")
DEFAULT_JOB_LOCATION = os.getenv("DEFAULT_JOB_LOCATION", "Remote")

# CORS configuration
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173")
ALLOW_ORIGINS = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

app = FastAPI(title="SmartCV Job Finder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    cv_text: str


class AnalysisResult(BaseModel):
    job_titles: List[str]
    skills: List[str]
    experience_level: str
    recommended_job_types: List[str]
    summary: Optional[str] = None


class FindJobsRequest(BaseModel):
    analysis: AnalysisResult
    location: Optional[str] = None
    limit: int = 20


class JobItem(BaseModel):
    title: str
    company: str
    location: str
    description: str
    apply_link: str
    source: Optional[str] = None


class FindJobsResponse(BaseModel):
    jobs: List[JobItem]


def extract_text_from_pdf(file: UploadFile) -> str:
    try:
        with pdfplumber.open(file.file) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
        text = "\n".join(pages_text)
        return text.strip()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {exc}") from exc


def extract_text_from_docx(file: UploadFile) -> str:
    try:
        file.file.seek(0)
        document = Document(file.file)
        paragraphs = [p.text for p in document.paragraphs]
        text = "\n".join(paragraphs)
        return text.strip()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse DOCX: {exc}") from exc


def extract_text_from_plain(file: UploadFile) -> str:
    try:
        file.file.seek(0)
        data = file.file.read()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1", errors="ignore")
        return text.strip()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {exc}") from exc


@app.post("/upload_cv")
async def upload_cv(file: UploadFile = File(...)) -> Dict[str, Any]:
    filename = file.filename or ""
    lower_name = filename.lower()

    if lower_name.endswith(".pdf"):
        text = extract_text_from_pdf(file)
    elif lower_name.endswith(".docx"):
        text = extract_text_from_docx(file)
    else:
        text = extract_text_from_plain(file)

    if not text:
        raise HTTPException(status_code=400, detail="No text could be extracted from the CV.")

    return {"text": text}



COMMON_SKILLS = [
    # Programming
    "python","java","javascript","typescript","c++","c#","php","ruby","go","rust","sql",
    # Web / frameworks
    "react","vue","angular","node.js","django","flask","fastapi","spring","laravel",
    # Data / ML
    "pandas","numpy","scikit-learn","tensorflow","pytorch","nlp","computer vision",
    # Cloud / devops
    "docker","kubernetes","aws","azure","gcp","ci/cd","git",
    # Other
    "excel","power bi","tableau","linux","bash"
]

COMMON_JOB_TITLES = [
    "software engineer","backend developer","frontend developer","full stack developer",
    "data analyst","data scientist","machine learning engineer","devops engineer",
    "product manager","project manager","ui/ux designer","qa engineer","cybersecurity analyst"
]

def analyze_cv_rule_based(cv_text: str) -> AnalysisResult:
    """No-API fallback: extracts rough signals from the CV text."""
    text = (cv_text or "").lower()

    # skills
    skills = sorted({s for s in COMMON_SKILLS if s.lower() in text})

    # job titles
    job_titles = sorted({t for t in COMMON_JOB_TITLES if t.lower() in text})

    # experience level heuristic
    years = []
    for m in re.finditer(r"(\d{1,2})\s*\+?\s*(?:years|yrs)\b", text):
        try:
            years.append(int(m.group(1)))
        except:
            pass
    max_years = max(years) if years else 0

    if "intern" in text or "student" in text:
        experience_level = "student"
    elif max_years >= 8:
        experience_level = "senior"
    elif max_years >= 3:
        experience_level = "mid"
    elif max_years > 0:
        experience_level = "junior"
    else:
        experience_level = "unknown"

    recommended_job_types = []
    if any(k in text for k in ["remote","work from home","wfh"]):
        recommended_job_types.append("remote")
    if any(k in text for k in ["part-time","part time"]):
        recommended_job_types.append("part-time")
    if any(k in text for k in ["full-time","full time"]):
        recommended_job_types.append("full-time")

    summary = "Rule-based analysis (no API key). " + (cv_text.strip()[:220] + ("..." if len(cv_text.strip())>220 else ""))

    return AnalysisResult(
        job_titles=job_titles,
        skills=skills,
        experience_level=experience_level,
        recommended_job_types=recommended_job_types or ["any"],
        summary=summary,
    )

def call_hf_for_analysis(cv_text: str) -> AnalysisResult:
    if not HF_TOKEN:
        return analyze_cv_rule_based(cv_text)
    """
    Use Hugging Face Inference API to analyze CV text and return structured data.
    """
    HF_MODEL = "facebook/bart-large-mnli"  # مثال: ممكن تستخدم أي نموذج تعليمي
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    prompt = (
        "Extract structured CV info in JSON format with keys: "
        "job_titles (list), skills (list), experience_level (junior/mid/senior/lead/executive/student), "
        "recommended_job_types (list), summary (1-2 sentences). "
        f"CV TEXT: {cv_text}"
    )

    payload = {"inputs": prompt}

    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HF_MODEL}",
            headers=headers,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        output = response.json()
        # نأخذ النص من النموذج
        text_out = output[0]["generated_text"] if isinstance(output, list) else str(output)
    except Exception as exc:
        # لو فشل الاتصال أو الرد
        text_out = ""

    import json
    try:
        data = json.loads(text_out)
    except Exception:
        data = {}

    # رجعنا defaults لو النموذج ما عطى بيانات
    job_titles = data.get("job_titles") or []
    skills = data.get("skills") or []
    experience_level = data.get("experience_level") or "unknown"
    recommended_job_types = data.get("recommended_job_types") or []
    summary = data.get("summary") or text_out.strip()

    if isinstance(job_titles, str):
        job_titles = [job_titles]
    if isinstance(skills, str):
        skills = [skills]
    if isinstance(recommended_job_types, str):
        recommended_job_types = [recommended_job_types]

    return AnalysisResult(
        job_titles=job_titles,
        skills=skills,
        experience_level=str(experience_level).lower(),
        recommended_job_types=recommended_job_types,
        summary=summary,
    )


@app.post("/analyze", response_model=AnalysisResult)
async def analyze(request: AnalyzeRequest) -> AnalysisResult:
    if not request.cv_text or len(request.cv_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="CV text is too short. Please upload a more detailed CV.")
    return call_hf_for_analysis(request.cv_text)


def search_jobs_adzuna(keywords: str, location: Optional[str], limit: int = 20) -> List[JobItem]:
    if not (ADZUNA_APP_ID and ADZUNA_APP_KEY):
        return []

    base_url = f"https://api.adzuna.com/v1/api/jobs/{ADZUNA_COUNTRY}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": keywords,
        "where": location or DEFAULT_JOB_LOCATION,
        "results_per_page": min(limit, 50),
        "content-type": "application/json",
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []

    results = []
    for item in payload.get("results", []):
        results.append(JobItem(
            title=item.get("title") or "Unknown Role",
            company=(item.get("company") or {}).get("display_name") or "Unknown Company",
            location=(item.get("location") or {}).get("display_name") or location or DEFAULT_JOB_LOCATION,
            description=item.get("description")[:400] if item.get("description") else "",
            apply_link=item.get("redirect_url") or "",
            source="Adzuna",
        ))

    return results


def build_keywords_from_analysis(analysis: AnalysisResult) -> str:
    """Build a compact keyword string to drive job searches."""
    parts: List[str] = []
    if analysis.job_titles:
        parts += analysis.job_titles[:3]
    if analysis.skills:
        parts += analysis.skills[:5]
    if analysis.recommended_job_types:
        parts += analysis.recommended_job_types[:2]

    seen = set()
    out: List[str] = []
    for p in parts:
        p = (p or "").strip()
        if not p:
            continue
        k = p.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(p)

    return " ".join(out)[:120] or "software developer"


def _strip_html(s: str) -> str:
    if not s:
        return ""
    # very small sanitizer for API descriptions
    s = re.sub(r"<\s*br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _keyword_match(keywords: str, hay: str) -> bool:
    if not keywords:
        return True
    hay_l = (hay or "").lower()
    tokens = [t for t in re.split(r"\s+", keywords.lower()) if t]
    # accept if any token matches (avoid over-filtering)
    return any(t in hay_l for t in tokens)


def _dedupe_jobs(jobs: List[JobItem], limit: int) -> List[JobItem]:
    seen = set()
    out: List[JobItem] = []
    for j in jobs:
        key = (j.apply_link or "").strip().lower() or f"{j.title}|{j.company}".lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
        if len(out) >= limit:
            break
    return out


def search_jobs_remotive(keywords: str, limit: int = 20) -> List[JobItem]:
    """Free API (no key). Must keep Remotive as source and link back to Remotive job URL."""
    url = f"https://remotive.com/api/remote-jobs?search={quote_plus(keywords)}&limit={min(limit, 50)}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        payload = r.json()
    except Exception:
        return []

    results: List[JobItem] = []
    for item in payload.get("jobs", []) or []:
        title = item.get("title") or "Unknown Role"
        company = item.get("company_name") or "Unknown Company"
        loc = item.get("candidate_required_location") or "Remote"
        desc = _strip_html(item.get("description") or "")
        link = item.get("url") or ""

        # minimal relevance filter
        if not _keyword_match(keywords, f"{title} {company} {desc} {loc}"):
            continue

        results.append(JobItem(
            title=title,
            company=company,
            location=loc,
            description=desc[:400],
            apply_link=link,
            source="Remotive",
        ))
        if len(results) >= limit:
            break
    return results


def search_jobs_remoteok(keywords: str, limit: int = 20) -> List[JobItem]:
    """Free feed. Must keep Remote OK as source and link back to the Remote OK job URL."""
    for base in ["https://remoteok.com/api", "https://remoteok.io/api"]:
        try:
            r = requests.get(base, timeout=20, headers={"User-Agent": "SmartCVJobFinder/1.0"})
            r.raise_for_status()
            payload = r.json()
            break
        except Exception:
            payload = None
    if not isinstance(payload, list):
        return []

    results: List[JobItem] = []
    # first element is usually metadata
    for item in payload[1:]:
        if not isinstance(item, dict):
            continue
        title = item.get("position") or item.get("title") or "Unknown Role"
        company = item.get("company") or "Unknown Company"
        loc = item.get("location") or "Remote"
        desc = _strip_html(item.get("description") or "")
        link = item.get("url") or ""

        tags = item.get("tags") or []
        tag_str = " ".join(tags) if isinstance(tags, list) else str(tags)

        if not _keyword_match(keywords, f"{title} {company} {loc} {tag_str} {desc}"):
            continue

        results.append(JobItem(
            title=title,
            company=company,
            location=loc,
            description=desc[:400],
            apply_link=link,
            source="Remote OK",
        ))
        if len(results) >= limit:
            break
    return results


def search_jobs_arbeitnow(keywords: str, limit: int = 20) -> List[JobItem]:
    """Free API (no key)."""
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        payload = r.json()
    except Exception:
        return []

    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        return []

    results: List[JobItem] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or "Unknown Role"
        company = item.get("company_name") or "Unknown Company"
        loc = item.get("location") or ""
        desc = _strip_html(item.get("description") or "")
        link = item.get("url") or ""

        tags = item.get("tags") or []
        tag_str = " ".join(tags) if isinstance(tags, list) else str(tags)

        if not _keyword_match(keywords, f"{title} {company} {loc} {tag_str} {desc}"):
            continue

        results.append(JobItem(
            title=title,
            company=company,
            location=loc or DEFAULT_JOB_LOCATION,
            description=desc[:400],
            apply_link=link,
            source="Arbeitnow",
        ))
        if len(results) >= limit:
            break
    return results


def mocked_jobs(analysis: AnalysisResult, location: str, limit: int) -> List[JobItem]:
    primary_title = (analysis.job_titles[0] if analysis.job_titles else None) or "Software Engineer"
    primary_type = (analysis.recommended_job_types[0] if analysis.recommended_job_types else None) or primary_title
    base_jobs = [
        JobItem(
            title=f"{primary_title} ({analysis.experience_level.title()} Level)",
            company="SmartCV Labs",
            location=location,
            description="Leverage your skills in a modern engineering environment.",
            apply_link="https://example.com/jobs/smartcv-labs",
            source="Mocked",
        ),
        JobItem(
            title=f"{primary_type} - Remote Friendly",
            company="FutureWork Global",
            location=location,
            description="Join a distributed team solving real-world problems.",
            apply_link="https://example.com/jobs/futurework-global",
            source="Mocked",
        ),
    ]
    return base_jobs[: max(1, min(limit, len(base_jobs)))]


@app.post("/find_jobs", response_model=FindJobsResponse)
async def find_jobs(request: FindJobsRequest) -> FindJobsResponse:
    analysis = request.analysis
    location = request.location or DEFAULT_JOB_LOCATION
    limit = max(1, min(request.limit, 50))

    keywords = build_keywords_from_analysis(analysis)

    # 1) Try real providers (free first, then Adzuna if configured)
    collected: List[JobItem] = []

    # Free providers (no keys)
    collected += search_jobs_remotive(keywords, limit)
    collected += search_jobs_remoteok(keywords, limit)
    collected += search_jobs_arbeitnow(keywords, limit)

    # Paid/Keyed provider (optional)
    collected += search_jobs_adzuna(keywords, location, limit)

    jobs = _dedupe_jobs(collected, limit)
    if not jobs:
        jobs = mocked_jobs(analysis, location, limit)

    return FindJobsResponse(jobs=jobs)


@app.get("/")
async def root():
    return {
        "message": "SmartCV Job Finder backend is running.",
        "endpoints": ["/upload_cv", "/analyze", "/find_jobs"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


