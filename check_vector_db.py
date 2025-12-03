import os
from chromadb import PersistentClient

CHROMA_DIR = "chroma_off"
COLLECTION_NAME = "bge_m3_embeddings"

def check_db():
    if not os.path.exists(CHROMA_DIR):
        print(f"Directory '{CHROMA_DIR}' does not exist. Database is empty.")
        return

    try:
        client = PersistentClient(path=CHROMA_DIR)
        try:
            collection = client.get_collection(COLLECTION_NAME)
        except Exception:
            print(f"Collection '{COLLECTION_NAME}' not found.")
            return

        print(f"--- Checking Vector Store ({COLLECTION_NAME}) ---")
        count = collection.count()
        print(f"Total Chunks: {count}")

        if count == 0:
            print("Database is empty.")
            return

        # Fetch all metadata to find unique destinations
        # Note: fetching all might be slow if huge, but fine for <10k chunks
        data = collection.get(include=["metadatas"])
        metadatas = data["metadatas"]
        
        destinations = set()
        for m in metadatas:
            if m and "destination" in m:
                destinations.add(m["destination"])
        
        print(f"\nFound {len(destinations)} Unique Destinations:")
        for d in sorted(destinations):
            print(f" - {d}")

    except Exception as e:
        print(f"Error reading database: {e}")

if __name__ == "__main__":
    check_db()
