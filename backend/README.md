# Backend

FastAPI product boundary for the AI Growth Agent. Run in `mock` mode for the credential-free portfolio demo or `dify` mode to proxy the published workflow.

```bash
pip install -r requirements-dev.txt
pytest
uvicorn app.main:app --reload
```

Configuration is documented in `.env.example`. Do not commit `.env` or expose the Dify application key to the frontend.

