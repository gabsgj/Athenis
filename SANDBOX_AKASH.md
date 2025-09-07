# Akash Sandbox (no custom Docker build)

**Goal:** Use a public base image, clone this repo, install minimal deps, run Gunicorn.

**Akash Sandbox Console fields:**
- Image: `python:3.11-slim`
- Expose:
  - Container Port: `8080`
  - As: `80`
  - To: `Global`
- Environment:
  - `API_KEY=change-me`
  - `FAST_TEST=1`
  - (optional) `CORS_ORIGINS=*`
- Command (multiline shell):

```
/bin/sh -lc "
apt-get update && apt-get install -y --no-install-recommends git curl && \
git clone https://github.com/<<YOUR_GITHUB_USERNAME>>/athenis.git /app && \
cd /app && pip install --no-cache-dir -r requirements-min.txt && \
gunicorn -w 2 -k gthread -b 0.0.0.0:8080 app.wsgi:application
"
```

Open the app at the Sandbox URL. Use the API key you set above in the UI.

**Notes**
- For real LLMs, set `EXTERNAL_LLM_API_URL` and keep `FAST_TEST` unset.
- Uploads work in single-container mode via `POST /gofr/ingest`.

---

# Exactly what to enter in Akash Sandbox Console (single container, "no Docker build")

**Image:** `python:3.11-slim`
**Command:**

```
/bin/sh -lc "
apt-get update && apt-get install -y --no-install-recommends git curl && \
git clone https://github.com/<<YOUR_GITHUB_USERNAME>>/athenis.git /app && \
cd /app && pip install --no-cache-dir -r requirements-min.txt && \
gunicorn -w 2 -k gthread -b 0.0.0.0:8080 app.wsgi:application
"
```

**Port:** container port `8080` → exposed as `80` (Global)
**Env:**

* `API_KEY=change-me`
* `FAST_TEST=1`
* (optional) `CORS_ORIGINS=*`

> If you **do** have an external LLM endpoint already, use:
>
> * `EXTERNAL_LLM_API_URL=https://your-llm.example.com/v1/infer`
>   and **unset** `FAST_TEST`.

---

# Why this works

* You're not building a custom image; you're using a public base (`python:3.11-slim`), cloning your repo at runtime, and launching Gunicorn — exactly what the Sandbox Console supports.
* You avoid huge HF downloads by using `requirements-min.txt` + `FAST_TEST=1`.
* Uploads don't depend on the Go sidecar anymore because we added `/gofr/ingest` in Flask.
* The front-end is told (via `window.APP_CONFIG`) to send uploads to `/gofr`, same origin, so CORS is not a problem.

---

If you want, say "next" and I'll give you a version where we switch over to **actual external LLM** mode (no stubs) and the exact `curl` your teammates can use to validate each endpoint before/after Sandbox deployment.
