import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Portkey Configuration
    PORT_KEY_API_KEY = os.getenv("PORT_KEY_API_KEY")
    PORT_KEY_ID = os.getenv("PORT_KEY_ID")

    NODE_API_URL = os.getenv("NODE_API_URL", "http://localhost:5000")

    # Firebase Credential Path (if needed for server-side verification,
    # but we might just pass the token to Node for verification)
    # FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")

settings = Settings()
