# Deploy ReportMaster AI (Vercel + Railway)

Public URL setup for this repo: **React on Vercel**, **FastAPI on Railway**, **SQLite + Chroma on a Railway volume**.

Local defaults are unchanged. You still run:

```bash
cd backend
uvicorn app.main:app --reload
```

```bash
cd frontend
npm start
```

---

## 1. Accounts

- [Railway](https://railway.app) (GitHub login)
- [Vercel](https://vercel.com) (GitHub login)
- [Google AI Studio](https://aistudio.google.com/apikey) for `GOOGLE_API_KEY`

Generate a JWT secret (PowerShell):

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 2. Backend — Railway

1. **New Project → Deploy from GitHub** → this repository.
2. Open the service → **Settings**:
   - **Root Directory:** `backend`  
     (required so Railway finds `requirements.txt`, `Procfile`, and `app/`)
   - **Start Command** (if not picked up automatically):

     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

3. **Resources:** set memory to **2 GB**. 512 MB usually crashes when MiniLM loads.
4. **Volumes:** add a volume, mount path `/data`.
5. **Variables** (Settings → Variables):

   | Variable | Value |
   |---|---|
   | `GOOGLE_API_KEY` | your Gemini key |
   | `SECRET_KEY` | output of `secrets.token_hex(32)` |
   | `DATABASE_URL` | `sqlite:////data/reportmaster.db` |
   | `CHROMA_PERSIST_DIR` | `/data/chroma_db` |
   | `MANUALS_DIR` | `/data/manuals` |
   | `HF_HOME` | `/data/hf_cache` |
   | `TRANSFORMERS_CACHE` | `/data/hf_cache` |
   | `SENTENCE_TRANSFORMERS_HOME` | `/data/hf_cache` |
   | `CORS_ORIGINS` | your Vercel URL after step 3, e.g. `https://your-app.vercel.app` |

   Until the frontend exists, you can temporarily set `CORS_ORIGINS=*`, then lock it to the Vercel origin.

6. **Networking → Generate Domain.** Copy the URL, no trailing slash:  
   `https://something.up.railway.app`
7. First deploy can take several minutes (pip + MiniLM download). Logs should show:

   ```
   Embedding model loaded: all-MiniLM-L6-v2
   ReportMaster AI is ready to serve queries.
   ```

8. Check:

   ```powershell
   curl https://YOUR-RAILWAY-URL/
   curl https://YOUR-RAILWAY-URL/api/health
   ```

The knowledge base starts **empty** (`collection_loaded: false`). After the UI is up, sign up and upload a text PDF, or run a one-off on Railway from `backend/`:

```bash
python scripts/ingest_data.py
```

---

## 3. Frontend — Vercel

1. **Add New → Project** → same GitHub repo.
2. Framework: **Create React App**.
3. **Root Directory:** `frontend`
4. Build: `npm run build` · Output: `build`
5. **Environment Variables:**

   | Variable | Value |
   |---|---|
   | `REACT_APP_API_URL` | `https://YOUR-RAILWAY-URL` (no trailing slash) |

   This is baked in at **build** time. If you change it, redeploy the frontend.

6. Deploy. Copy the URL: `https://your-app.vercel.app`
7. Go back to Railway and set:

   ```
   CORS_ORIGINS=https://your-app.vercel.app
   ```

   Restart the Railway service if it does not pick up the variable automatically.

`frontend/vercel.json` rewrites unknown paths to `index.html` so `/login`, `/dashboard`, and `/query` work on refresh.

---

## 4. Verify

1. `GET https://api…/` → `{"message":"ReportMaster AI is running"}`
2. Open the Vercel URL → login page (not API JSON)
3. Sign up → dashboard
4. Upload a **text** PDF (scanned PDFs extract 0 pages)
5. Ask a question → answer + source cards
6. Refresh `/query` → page still loads
7. Incognito `/dashboard` → redirect to `/login`

---

## 5. Common errors

| Symptom | Fix |
|---|---|
| Railway crash on boot / OOM | Raise memory to 2 GB |
| 503 on every query | Empty Chroma — upload a PDF or run ingest |
| Frontend “Network error” | Wrong `REACT_APP_API_URL` or frontend not rebuilt |
| Browser CORS error | `CORS_ORIGINS` must be the exact Vercel origin (`https`, no slash) |
| `/query` 404 on refresh | Confirm `frontend/vercel.json` is deployed |
| Users or index vanish after redeploy | Volume not mounted, or paths not under `/data` |
| Query 401 after restart | `SECRET_KEY` changed — log in again |

---

## 6. What this repo does **not** do

- No Postgres. Users stay in SQLite on the volume.
- No Docker. Railway Nixpacks installs `backend/requirements.txt`.
- No Alembic migrations. `create_all` runs on boot (creates `users` if missing).
- `/api/ingest` is unauthenticated — anyone who knows the API URL can trigger a rebuild.
