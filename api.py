import os
import traceback
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
import uvicorn
from app.core.state_machine import ChatStateMachine

# -----------------------------
# CONFIG
# -----------------------------
CHROMA_DIR = "chroma_off"
COLLECTION_NAME = "bge_m3_embeddings"
MODEL_NAME = "BAAI/bge-m3"

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("Starting up... triggering model load.")
    # Load model in background or blocking? Blocking is safer for now to ensure readiness.
    # If we want faster startup, we can use asyncio.create_task, but then requests might fail early.
    # Given the issue is import-time hang, blocking here is fine as uvicorn is already running.
    vector_store.load_model()

# -----------------------------
# Load Model & DB (via Singleton)
# -----------------------------
from app.services.vector_store import vector_store

# -----------------------------
# Request Models
# -----------------------------
class SearchRequest(BaseModel):
    query: str
    top_k: int = 3

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/")
def health_check():
    return {
        "status": "ok", 
        "model_loaded": vector_store.model is not None, 
        "db_connected": vector_store.collection is not None
    }

@app.post("/search")
def search(request: SearchRequest):
    if not vector_store.model:
        raise HTTPException(status_code=500, detail="Model not loaded")
    if not vector_store.collection:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        print(f"Processing query: {request.query}")
        
        # 1. Generate Embedding
        query_embedding = vector_store.model.encode(request.query, normalize_embeddings=True).tolist()

        # 2. Query ChromaDB
        results = vector_store.collection.query(
            query_embeddings=[query_embedding],
            n_results=request.top_k,
            include=["metadatas", "documents", "distances"]
        )

        # 3. Format Results
        formatted_results = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "destination": results["metadatas"][0][i].get("destination"),
                    "chunk_num": results["metadatas"][0][i].get("chunk_num"),
                    "text": results["documents"][0][i],
                    "distance": results["distances"][0][i]
                })

        return {"results": formatted_results}

    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, token: str):
    print(f"=== WebSocket connection attempt with token: {token[:20]}...")
    await websocket.accept()
    print(f"=== WebSocket accepted ===")
    
    # Initialize State Machine for this connection
    try:
        print("Initializing ChatStateMachine...")
        sm = ChatStateMachine(token=token)
        print("ChatStateMachine initialized successfully")
    except Exception as e:
        print(f"ERROR: Failed to initialize ChatStateMachine: {e}")
        traceback.print_exc()
        await websocket.send_text(f"Server error: Could not initialize chat. {str(e)}")
        await websocket.close()
        return
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"=== Received message: {data} ===")
            
            try:
                # Process message through State Machine
                response_count = 0
                async for response in sm.handle_message(data):
                    response_count += 1
                    print(f"Sending response #{response_count}: {response[:100]}...")
                    await websocket.send_text(response)
                print(f"=== Sent {response_count} responses ===")
            except Exception as msg_error:
                print(f"ERROR processing message: {msg_error}")
                traceback.print_exc()
                await websocket.send_text(f"Error: {str(msg_error)}")
                
    except WebSocketDisconnect:
        print("=== WebSocket disconnected by client ===")
    except Exception as e:
        print(f"=== WebSocket Error: {e} ===")
        traceback.print_exc()
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
