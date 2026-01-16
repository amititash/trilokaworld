import sys
import os
import traceback

# Add /app to python path
sys.path.append("/app")

try:
    print("Attempting to import ChatStateMachine...")
    from app.core.state_machine import ChatStateMachine
    print("Import successful.")
    
    print("Attempting to initialize ChatStateMachine...")
    sm = ChatStateMachine(token="debug_token")
    print("Initialization successful!")
    
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    traceback.print_exc()
