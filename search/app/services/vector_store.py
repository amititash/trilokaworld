import os
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer

class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.model = None
        self.client = None
        self.collection = None
        self.chroma_dir = "chroma_off"
        self._initialized = True
        print("Vector Store Object Created (Lazy Init)")

    def load_model(self):
        if self.model:
            print("Model already loaded.")
            return

        print("Loading Vector Store Model (BGE-M3)...")
        
        # Load model
        try:
            print("Loading BAAI/bge-m3 model (matching database)...")
            self.model = SentenceTransformer("BAAI/bge-m3")
            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
        
        # Connect to Chroma
        try:
            self.client = PersistentClient(path=self.chroma_dir)
            self.collection = self.client.get_collection("bge_m3_embeddings")
            print("Connected to ChromaDB collection: bge_m3_embeddings")
        except Exception as e:
            print(f"Warning: Could not connect to bge_m3_embeddings: {e}")
            try:
                self.collection = self.client.get_collection("minilm_embeddings")
                print("Connected to minilm_embeddings as fallback")
            except Exception as e2:
                print(f"Error: Could not connect to any collection: {e2}")
                self.collection = None
        
        print("Vector Store Resources Loaded.")

    def search(self, query_text: str, top_k: int = 3):
        """
        Search the vector DB for relevant documents.
        Returns a list of dicts with 'text', 'destination', 'distance'.
        """
        try:
            # Encode query
            qvec = self.model.encode(query_text, normalize_embeddings=True).tolist()
            
            # Query Chroma
            results = self.collection.query(
                query_embeddings=[qvec],
                n_results=top_k,
                include=["documents", "distances", "metadatas"]
            )
            
            if not results["documents"] or not results["documents"][0]:
                return []

            docs = results["documents"][0]
            distances = results["distances"][0]
            metas = results["metadatas"][0]
            
            formatted_results = []
            for doc, dist, meta in zip(docs, distances, metas):
                # Distance threshold? Chroma uses L2 or Cosine distance depending on setup.
                # Usually smaller distance = better match.
                # Let's just return everything for now and let caller decide or filter.
                formatted_results.append({
                    "text": doc,
                    "destination": meta.get("destination"),
                    "distance": dist
                })
                
            return formatted_results

        except Exception as e:
            print(f"Vector Search Error: {e}")
            return []

# Singleton instance
vector_store = VectorStore()
