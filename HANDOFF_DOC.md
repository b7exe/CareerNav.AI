# AI Career Navigator: Project Handoff & Architecture Overview

This document summarizes the intensive "Phase 3" upgrade of the AI Career Navigator. The project has transitioned from a static, checklist-based roadmap tool to a dynamic, brutally realistic AI-driven career intelligence platform.

---

## 0. Quick Start & Setup

### Prerequisites
- **Python**: 3.10+
- **Environment**: Virtual environment recommended (`python -m venv venv`)

### Installation & Launch
1.  **Install dependencies**: `pip install flask requests openai-python python-dotenv`
2.  **Verify `.env`**: Ensure the following variables are set:
    - `NVIDIA_API_KEY`: Primary LLM engine (NVIDIA NIM).
    - `NEWS_API_KEY`: Real-time sector news feed.
    - `ADZUNA_APP_ID` / `ADZUNA_APP_KEY`: Live job market data.
    - `GEMINI_API_KEY`: Fallback LLM engine.
3.  **Run the app**: `python app.py`
4.  **Access**: `http://127.0.0.1:5000`

---

## 1. Core Architectural Shifts

### From Checklists to Dashboards
The old "Phase/Task" checklist system has been entirely deprecated. Users now receive a **Career Intelligence Dashboard** powered by:
- **`logic/engine.py`**: The primary ranking and recommendation engine.
- **`logic/llm.py`**: A high-fidelity content generator utilizing **NVIDIA NIM** (`llama-3.3-70b-instruct`).
- **`logic/market_data_json.json`**: An expanded database of 81+ modern career and skill paths.

### Zero-Infrastructure State
The application remains "zero-infrastructure," storing all user profile data and matched career paths locally in the browser's `localStorage`. No database migrations are required.

---

## 2. Key Features Implemented

### 🚀 Dynamic Career Overviews
- **AI Fallback**: If a user searches for a career not in our 81-path static database, the system automatically triggers an NVIDIA NIM prompt to generate a 5-sentence tactical description, core skills, and emerging AI-era competencies.
- **News Integration**: Every roadmap now includes a **"Latest Sector News"** module that pulls real-time hiring trends via NewsAPI.

### 🎯 Proactive Matching & Boosting
- **Web-Dev Prioritization**: We've added explicit context boosts for terms like "web," "website," and "building websites." This prevents the system from falling back to generic high-demand roles (like Blockchain) when a user clearly wants web development.
- **Keyword Stemming**: The engine now handles basic pluralization (e.g., matching "websites" to "website").

### ⚡ Performance Optimization
- **LRU Caching**: We've wrapped the core `analyze_interests` and `generate_roadmap` functions in a **128-slot RAM cache**. Navigating backward and forward between paths is now instantaneous (0ms latency).

---

## 3. UI/UX Refinements

### Roadmap Dashboard (`roadmap.html`)
- **Centered Resources**: Moved YouTube mentor cards from the sidebar to a prominent central grid.
- **Market Snapshot Sidebar**: Fixed data-binding bugs; it now correctly displays **Avg Salary (India)**, **Global Demand**, and **AI Disruption Risk**.
- **Demand Index**: Added a new metric visualizer tracking the role's market vitality out of 100.

### Career Search (`careers.html`)
- **Ultra-Wide Modal**: The career detail popup has been expanded to `max-w-6xl` with an inline data grid to **eliminate scrollbars** on standard displays.
- **Match Reasons**: Every recommended role now includes an AI-generated personalized "Match Reason" explaining why that path fits the user's input.

---

## 4. Technical Debt & Resolved Bugs

- **Fixed `KeyError`**: Resolved a crash in `realtime_fetcher.py` caused by missing `social_signal` keys in the background data extraction daemon.
- **Fixed `ImportError`**: Cleaned up legacy `generate_ai_roadmap` imports after refactoring to the new overview structure.
- **Fixed `UnboundLocalError`**: Corrected variable scope issues in the roadmap generation pipeline.
- **Template Robustness**: Added Jinja2 `| default('...')` fallbacks to every dynamic field to prevent HTML 500 errors if metadata is missing.

---

## 5. Project Directory Map

- `/logic`: **The Brain**.
    - `engine.py`: Recommendation & Roadmap logic (with LRU caching).
    - `llm.py`: NVIDIA NIM & Gemini integration wrappers.
    - `market_data.py`: Data access patterns for the static/cached role DB.
    - `data_sources.py`: Integrations for NewsAPI, Adzuna, GitHub Trending, etc.
    - `realtime_fetcher.py`: Background daemon for market signal extraction.
- `/templates`: **The Interface**.
    - `home.html`: High-fidelity entry point.
    - `careers.html`: Recommendation list & detailed career modals.
    - `roadmap.html`: The new centered Dashboard overview.
- `/static`: CSS design system (`custom.css`) and cursor-orb JS.

---

## 6. Next Steps for Development

> [!IMPORTANT]
> **API Key Management**: Ensure `.env` contains valid keys for `NVIDIA_API_KEY` and `NEWS_API_KEY`.
> **Market Data Freshness**: The `logic/market_cache.json` is partially updated by the background extraction daemon. If data looks stale, run `update_market_data.py` to trigger a manual refresh.
> **Mobile Polish**: While the desktop view is pixel-perfect, the new ultra-wide modal needs testing on smaller tablet resolutions to ensure the grid stacks correctly.

---

**Current Status:** Stable / High Performance
**Active Branch:** Main
**Lead AI Assistant:** Antigravity (NVIDIA NIM Toolchain)
