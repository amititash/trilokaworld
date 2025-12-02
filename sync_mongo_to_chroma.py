import os
import pymongo
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

# Config
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
DB_NAME = "ai_travel"
CHROMA_DIR = "chroma_off"
COLLECTION_NAME = "bge_m3_embeddings"
MODEL_NAME = "BAAI/bge-m3"

def sync():
    print("Connecting to MongoDB...")
    client_mongo = pymongo.MongoClient(MONGO_URI)
    db = client_mongo[DB_NAME]
    destinations_col = db["destinations"]
    
    destinations = list(destinations_col.find({}))
    if not destinations:
        print("No destinations found in MongoDB! Make sure you have seeded the database.")
        return

    print(f"Found {len(destinations)} destinations in MongoDB.")

    # 2. Prepare Chunks
    all_chunks = []
    
    for dest in destinations:
        name = dest.get("name")
        details = dest.get("details", {})
        
        # Also add description as a chunk
        if dest.get("description"):
            all_chunks.append({
                "id": f"{name}__desc",
                "text": dest["description"],
                "destination": name,
                "section": "Overview",
                "words": len(dest["description"].split())
            })
            
        for section, text in details.items():
            if not text: continue
            # If text is too long, maybe split? For now, assume sections are reasonable.
            # BGE-M3 handles long context well (8192 tokens), so usually fine.
            # Split by double newline (paragraphs) or single newline if that's how it's stored
            # Since import_destination joins with \n, we can split by \n
            paragraphs = text.split('\n')
            
            para_buffer = []
            chunk_counter = 0
            
            for para in paragraphs:
                para = para.strip()
                if not para: continue
                
                # Simple grouping: if para is short, maybe combine? 
                # For now, let's just treat each non-empty line/para as a chunk or combine small ones
                # Logic similar to chunks_clean:
                
                all_chunks.append({
                    "id": f"{name}__{section}_{chunk_counter}",
                    "text": para,
                    "destination": name,
                    "section": section,
                    "words": len(para.split())
                })
                chunk_counter += 1

    print(f"Generated {len(all_chunks)} chunks.")

    # 3. Load Model
    print(f"Loading {MODEL_NAME} model...")
    model = SentenceTransformer(MODEL_NAME)

    # 4. Connect to Chroma
    client_chroma = PersistentClient(path=CHROMA_DIR)
    try:
        client_chroma.delete_collection(COLLECTION_NAME)
        print("Deleted existing collection.")
    except:
        pass
        
    collection = client_chroma.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    # 5. Embed and Store
    batch_size = 10
    for i in tqdm(range(0, len(all_chunks), batch_size), desc="Syncing to Chroma"):
        batch = all_chunks[i:i+batch_size]
        texts = [c["text"] for c in batch]
        ids = [c["id"] for c in batch]
        metadatas = [{
            "destination": c["destination"],
            "section": c["section"],
            "words": c["words"]
        } for c in batch]
        
        embeddings = model.encode(texts, normalize_embeddings=True).tolist()
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=texts
        )

    print("\nSync Complete! AI is now using data from MongoDB.")

if __name__ == "__main__":
    sync()
