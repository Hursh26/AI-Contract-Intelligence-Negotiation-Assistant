# Fineprint — frontend-ui

Alternative UI prototype that lives beside the existing `frontend/` app (that one runs on :5173, this one on :3000).

React 19 + Vite + TypeScript + Tailwind v4. Talks to the FastAPI backend in `../backend`.

## Quick start

You need Git, **Python 3.11 or 3.12** and Node.js 20.19+. Do not use Python 3.14 (or any Python much newer than 3.12): the backend's pinned packages have no ready-made installs for it and `pip install` fails. Use **two terminal windows**, both starting in the project's root folder. The backend must be running before you use the UI.

### Window 1: backend (port 8000)

First time only: create the environment **and install the packages** (skipping the install is the most common reason nothing works).

```bash
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt      # Mac/Linux: .venv/bin/python -m pip ...
```

Every time. This uses a simple file database, so PostgreSQL is not needed. Keep the file outside the project so it is never committed.

```bash
# Windows Command Prompt (cmd):
set DATABASE_URL=sqlite:///C:/Users/YOUR-NAME/contract-dev.db
# Windows PowerShell:
$env:DATABASE_URL = "sqlite:///$($env:USERPROFILE.Replace('\','/'))/contract-dev.db"
# Mac/Linux:
export DATABASE_URL="sqlite:///$HOME/contract-dev.db"

.venv\Scripts\python -m app.db.init_db                            # Mac/Linux: .venv/bin/python ...
.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

Check it: http://localhost:8000/api/v1/health should show `{"status":"ok"}`. The `DATABASE_URL` line only lasts for that window, so set it again in every new window.

### Window 2: this UI (port 3000)

```bash
cd frontend-ui
npm install            # first time only
npm run dev            # http://localhost:3000, proxies /api to http://localhost:8000
```

Open http://localhost:3000 and click "try a sample contract". `npm run build` runs the typecheck and a production build.

Override the proxy target with `VITE_BACKEND_URL`. For a production build served from another origin, set `VITE_API_URL` (see `.env.example`) and allow that origin in the backend CORS list.

### Optional: ML service (port 8001)

Only needed for the real analysis. Without it the app still works and shows an example analysis, with a note on the page. See `../ml/README.md` (large install, slow first run).

## Troubleshooting

| What you see | Cause and fix |
|---|---|
| "We cannot connect right now…" (in dev it adds a hint about port 8000) | The backend is not running. Start Window 1 and check the health link above. |
| `pip install` ends with `Failed building wheel for pydantic-core` | Your Python is too new (e.g. 3.14). Install Python 3.12, delete the `backend\.venv` folder, then recreate it with `py -3.12 -m venv .venv` and run the install again. |
| Backend window says `No module named 'fastapi'` (or another package) | The packages were never installed. Run the `pip install -r requirements-dev.txt` line from the first-time step. |
| Backend window says it cannot connect to PostgreSQL | `DATABASE_URL` is not set in that window. Set it again (it does not carry over between windows). |
| "address already in use" for port 8000 or 3000 | An old server is still running. Stop it with Ctrl+C, or find it with `netstat -ano \| findstr :8000` and end it with `taskkill /PID <number> /F`. |
## Pages

| Route | What it does |
|---|---|
| `/` | Upload (drag and drop, file picker, or the sample contract), recent contracts |
| `/c/:id/reading` | Loading screen: extract the text, then run the analysis |
| `/c/:id` | Overview: summary, risk score, key facts, clauses to look at first |
| `/c/:id/review` | Contract text, clause list with risk filter, explanation, "Ask this contract" |
| `/c/:id/negotiate` | Accept or drop suggested changes, email draft, marked-up copy download |

## What is real and what is demo

| Feature | Source |
|---|---|
| Upload, validation errors, text extraction, contract fetch | Real backend (`src/lib/api.ts`) |
| Clauses, risk levels, risk score, key facts | Real: `POST /analyze` then `GET /analysis` (backend `develop` + ML service) |
| Ask answers | Real: `POST /ask` |
| Plain-language explanations and suggested wording | **Built-in examples** (keyword rules in `src/lib/analysis.ts`); the ML service does not produce these |
| Recent contracts | Browser `localStorage` only (see below) |

If the analysis endpoints are missing (older backend) or the ML service is down, the app keeps working with the built-in preview analysis and the page banner says so.

## Recent contracts

- Kept in this browser only. `GET /contracts` is deliberately **not** used: it lists everyone's contracts and there is no login yet.
- One row per document: uploading the same file name again replaces its earlier entry (case-insensitive).
- Keeps the last 10 (`MAX_RECENT` in `src/lib/recent.ts`); older ones drop off.
- Each row has an × to remove it, and "Clear all" asks for a second click. This only clears the list on this device: the backend has no delete endpoint, so uploaded files stay on the server.

## Where things are

```
src/
├── lib/api.ts          # backend calls and plain-language error messages
├── lib/analysis.ts     # turns backend analysis into what the pages show (and the built-in fallback)
├── lib/recent.ts       # recent contracts (localStorage)
├── lib/sample.ts       # synthetic sample contract for the "try a sample" button
├── components/ui.tsx   # cursor, magnetic buttons, reveal animations, risk tags
├── pages/              # Home, Reading, ContractLayout, Overview, Review, Negotiate
└── index.css           # design tokens and motion styles
```

## Testing notes

- No automated tests yet, and CI has no frontend job. Check `npm run build` passes and click through the flow above.
- Layout was checked from 320px to 1920px wide. Not yet checked on real phones, with keyboard-only navigation, or in Safari and Firefox.
- The real ML service has not been tested with this UI; only a stand-in that follows the backend's `ml_client.py` contract.
- Use only synthetic contracts for testing (see `CONTRIBUTING.md`).
