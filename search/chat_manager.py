from datetime import datetime
from typing import Dict, List

# Message store: token -> list of messages sorted by created_at
chats: Dict[str, List[Dict]] = {}

def add_message(token: str, message: str, role: str = "user"):
    """Add a message to the chat history for a given token."""
    if token not in chats:
        chats[token] = []

    message_obj = {
        "role": role,
        "content": message,
        "created_at": datetime.now()
    }
    chats[token].append(message_obj)
    return message_obj

def get_messages(token: str, k: int = None) -> List[Dict]:
    """Get the last k messages for a token in ascending order (oldest to newest).

    Args:
        token: The chat token
        k: Number of recent messages to return. If None, returns all messages.
    """
    if token not in chats:
        return []

    messages = chats[token]
    # Sort by created_at in ascending order
    sorted_messages = sorted(messages, key=lambda x: x["created_at"])

    # Get last k messages if specified
    if k is not None:
        sorted_messages = sorted_messages[-k:]

    # Remove created_at from returned messages
    return [{k: v for k, v in msg.items() if k != "created_at"} for msg in sorted_messages]

def clear_messages(token: str):
    """Clear all messages for a given token."""
    if token in chats:
        del chats[token]
