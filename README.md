# SmartTour Search Service

This is the Python-based AI service for SmartTour, powered by FastAPI.
It handles:
- RAG (Retrieval Augmented Generation) using ChromaDB.
- Real-time Chat via WebSockets.
- LLM Integration (Gemini/OpenAI).

## Setup

1.  **Create Virtual Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Mac/Linux
    # .venv\Scripts\activate  # Windows
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Variables**:
    Create a `.env` file (see `.env.example`) with:
    - `GEMINI_API_KEY` or `OPENAI_API_KEY`
    - `NODE_API_URL` (default: http://localhost:5000)

## Running

```bash
uvicorn api:app --reload --port 8000
```

## Docker

```bash
docker build -t smarttour-search .
docker run -p 8000:8000 --env-file .env smarttour-search
```
