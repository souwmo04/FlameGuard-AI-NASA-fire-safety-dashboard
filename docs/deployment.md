# Deployment

FlameGuard has two parts, deployed separately:

| Part | What it is | Recommended free host |
|---|---|---|
| API (`Dockerfile`) | FastAPI + model + data + Ask FlameGuard search | **Hugging Face Spaces** (Docker, CPU Basic: 2 vCPU, 16 GB RAM) |
| Website (`frontend/`) | Next.js app, all pages static | **Vercel** (Hobby) |

The API peaks at about **410 MB** of memory with the embedding model loaded, measured locally. That is why free
512 MB instances (for example Render Free) are not recommended. `render.yaml` is included for a paid Render
instance.

Both parts need each other's URL, so deploy the API first.

## 1. API on Hugging Face Spaces

1. Create an account at <https://huggingface.co>, then **New Space** → SDK **Docker** → template **Blank** →
   hardware **CPU Basic (free)**. Name it, e.g. `flameguard-api`.
2. In the Space's **Settings → Variables and secrets**, add:

   | Name | Type | Value |
   |---|---|---|
   | `FLAMEGUARD_CORS_ORIGINS` | variable | your website URL, e.g. `https://flameguard.vercel.app` (comma-separate several) |
   | `FLAMEGUARD_LLM_API_KEY` | **secret** | your free Groq key (optional; without it Ask FlameGuard shows cited passages only) |
   | `FLAMEGUARD_ASK_PER_MINUTE` | variable | `6` |

3. Push this repository to the Space. The YAML header at the top of `README.md` tells Hugging Face to build the
   root `Dockerfile` and route traffic to port 8000. Hugging Face asks for an access token with write permission
   as the password.

   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/flameguard-api
   git push --force space main
   ```

   `--force` is needed only for this first push: it replaces the placeholder files the new Space starts with.
   Never force-push to your GitHub remote.

4. Wait for the build (about 5–10 minutes the first time), then open
   `https://<your-username>-flameguard-api.hf.space/api/health`. It should return `"status": "ok"`. The
   interactive API docs are at `/docs`.

Free Spaces sleep after a period without traffic; the first request afterwards takes a minute while the Space
wakes up. To redeploy after changes, run `git push space main` again.

## 2. Website on Vercel

1. Sign in at <https://vercel.com> with GitHub and **Add New → Project** → import this repository.
2. Set **Root Directory** to `frontend`. Vercel detects Next.js automatically.
3. Add the environment variable `NEXT_PUBLIC_API_URL` = `https://<your-username>-flameguard-api.hf.space` (no
   trailing slash). It is read at build time, so redeploy after changing it.
4. Deploy. Every push to `main` then redeploys the site automatically.
5. Put the final site URL into the Space's `FLAMEGUARD_CORS_ORIGINS` variable. Hugging Face restarts the Space
   when a variable changes.

## 3. Check the live site

- The landing page shows live counts (274 tests). If it shows an API error, check `NEXT_PUBLIC_API_URL` and
  `FLAMEGUARD_CORS_ORIGINS`.
- `/risk` → Analyze returns a Fire Risk score, and methanol scenarios show the contamination check.
- `/knowledge` → the badge shows the model name (key set) or "Retrieval only" (no key).

## Alternatives

- **Render:** connect the repository; `render.yaml` defines the service. Use at least the Starter plan.
- **Any container host** (Fly.io, Google Cloud Run, Azure Container Apps):

  ```bash
  docker build -t flameguard-api .
  docker run -p 8000:8000 -e FLAMEGUARD_CORS_ORIGINS=https://your-site -e FLAMEGUARD_LLM_API_KEY=... flameguard-api
  ```

  The container listens on `$PORT` (default 8000) and has a health check on `/api/health`.

## What the image contains

Only what the API serves: `backend/app`, the `flameguard` library, `data/processed`, `data/knowledge`, the final
model and `reports/`. The embedding model is downloaded once at build time. Raw NASA files, the 41 MB PDF,
notebooks, the frontend and tests are excluded (`.dockerignore`). XGBoost, SHAP and matplotlib are research-only
dependencies and are not installed.

## Secrets

Keys live only in `backend/.env` (git-ignored) locally, and in the host's secret store when deployed. The API
never returns or logs the key (`/api/ask/status` reports only whether one is configured).
