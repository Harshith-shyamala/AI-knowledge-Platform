# EAKP Streamlit MVP

Streamlit UI for demoing the Enterprise AI Knowledge Platform backend.

## Run

From `enterprise-ai-platform`:

```bash
python3 -m venv backend/.venv
. backend/.venv/bin/activate
pip install -r backend/requirements-dev.txt
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

The UI expects the FastAPI backend at `http://127.0.0.1:8000` by default.
