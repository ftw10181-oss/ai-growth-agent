# Backend

FastAPI product boundary for the AI Growth Agent. Run in `mock` mode for the credential-free portfolio demo or `dify` mode to proxy the published workflow.

The frontend-facing endpoint is `POST /api/analyze`. The original versioned path, `POST /api/v1/insights`, remains available as a compatibility alias.

```bash
pip install -r requirements-dev.txt
pytest
uvicorn app.main:app --reload
```

Configuration is documented in `.env.example`. Do not commit `.env` or expose the Dify application key to the frontend.
