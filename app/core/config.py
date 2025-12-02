import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "gemini")  # "gemini" or "openai"
    NODE_API_URL = os.getenv("NODE_API_URL", "http://localhost:5000")
    
    # Firebase Credential Path (if needed for server-side verification, 
    # but we might just pass the token to Node for verification)
    # FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")

settings = Settings()
