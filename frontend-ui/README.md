# Fineprint — frontend-ui

Alternative UI prototype that lives beside the existing `frontend/` app (that one runs on :5173, this one on :3000).

React 19 + Vite + TypeScript + Tailwind v4. Talks to the FastAPI backend in `../backend`.

```bash
cd frontend-ui
npm install
npm run dev        # http://localhost:3000, proxies /api to http://localhost:8000
npm run build      # typecheck + production build
```

Start the backend first (see `../backend/README.md`). Override the proxy target with `VITE_BACKEND_URL`.

## What is real and what is demo

| Feature | Source |
|---|---|
| Upload, validation errors, text extraction, contract fetch | Real backend (`src/lib/api.ts`) |
| Clauses, risk levels, risk score, key facts | Real: `POST /analyze` then `GET /analysis` (backend `develop` + ML service) |
| Ask answers | Real: `POST /ask` |
| Plain-language explanations and suggested wording | **Built-in examples** (keyword rules in `src/lib/analysis.ts`); the ML service does not produce these |
| Recent contracts | Browser `localStorage`, last 10, removable. Not `GET /contracts`: it lists everyone's contracts and there is no login yet |

If the analysis endpoints are missing (older backend) or the ML service is down, the app keeps working with the built-in preview analysis and the page banner says so.
