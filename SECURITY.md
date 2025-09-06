# Security Notes

- API key required for all endpoints. Set `API_KEY` in env.
- CORS limited via Flask-CORS and CSP headers in `app/utils/security.py`.
- No credentials are committed. Use environment variables and GitHub Secrets.
- SSE streams do not include secrets.
- Redis cache optional; if used, protect `REDIS_URL` and deploy on private network.
