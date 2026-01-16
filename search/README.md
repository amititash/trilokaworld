# SmartTour Search Service (AI)

This is the Python-based AI service for SmartTour. It powers the intelligent chat, itinerary generation, and vector search capabilities using FastAPI, ChromaDB, and Google Gemini.

## 📂 Folder Structure

- **`app/`**: Main application code
  - **`core/`**: Core logic
    - **`state_machine.py`**: Manages chat state and flow.
    - **`config.py`**: Environment configuration.
  - **`services/`**: External service integrations
    - **`llm_client.py`**: Interface for Gemini/OpenAI (Generates text/JSON).
    - **`node_client.py`**: Interface for the Node.js Backend (Saves trips/prefs).
    - **`vector_store.py`**: Manages ChromaDB and Embeddings.
- **`api.py`**: FastAPI entry point (Web server & WebSocket endpoint).
- **`import_destination.py`**: Script to parse text files and save destinations to MongoDB.
- **`sync_mongo_to_chroma.py`**: Script to generate embeddings from MongoDB data and store in ChromaDB.
- **`easy_import.py`**: Helper script to automate data import.
- **`debug_chat.py`**: Script for testing chat logic locally.

## 🚀 How to Run

### Prerequisites
- Python 3.9+
- ChromaDB (runs in-process or via Docker)
- Gemini API Key

### Local Development
1.  Create virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Start the server:
    ```bash
    python api.py
    ```
    Server runs on `http://localhost:8000`.

### Data Management
- **Add New Destination**:
  ```bash
  python easy_import.py ./path/to/destination.txt "https://image-url.com"
  ```
- **Update AI Memory**:
  ```bash
  python sync_mongo_to_chroma.py
  ```

## 🔑 Key Environment Variables (`.env.prod`)
- `GEMINI_API_KEY`: API key for Google Gemini.
- `NODE_API_URL`: URL of the Node.js backend (e.g., `http://backend:5000`).
- `MODEL_PROVIDER`: Set to `gemini`.
