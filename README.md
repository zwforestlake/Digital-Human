# Digital Human Video Pipeline

Vue 3 + FastAPI project scaffold for a short-video rewriting, voice generation, lip-sync, subtitle QA, cover design, and local export workflow.

## What is included

- Vue 3 + Vite + TypeScript frontend scaffold.
- FastAPI backend scaffold.
- Step-specific model configuration in `backend/app/core/model_config.yaml`.
- Local task orchestration API with progress polling.
- Placeholder services for Douyin ingestion, script extraction, rewriting, TTS, lip-sync, subtitle QA, cover generation, and export.

The first implementation is intentionally structured as an MVP shell. It is ready for replacing placeholders with real DashScope/Qwen, ASR, TTS, and lip-sync calls.

## Quick Start

Backend:

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## API Key

Put the DashScope/Qwen key only in the backend `.env` file:

```env
DASHSCOPE_API_KEY=your_api_key_here
```

Never expose model API keys in the Vue frontend.
