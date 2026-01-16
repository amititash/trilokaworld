from datetime import datetime
from typing import Dict, Optional

# User context store: token -> user context
user_contexts: Dict[str, Dict] = {}

def get_user_context(token: str) -> Dict:
    """Get the user context for a given token.

    Args:
        token: The user token

    Returns:
        User context dict with destination, days, preferences, itinerary, and trip_id
    """
    if token not in user_contexts:
        # Initialize new user context with default values
        user_contexts[token] = {
            "destination": None,
            "days": None,
            "preferences": None,
            "itinerary": None,
            "trip_id": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

    return user_contexts[token]

def update_user_context(token: str, context: Optional[Dict] = None):
    """Update the user context for a given token.

    Args:
        token: The user token
        context: Context data to update (will merge with existing)
    """
    if token not in user_contexts:
        get_user_context(token)  # Initialize if doesn't exist

    if context is not None:
        # Merge context updates (excluding timestamps)
        for key, value in context.items():
            if key not in ["created_at", "updated_at"]:
                user_contexts[token][key] = value

    user_contexts[token]["updated_at"] = datetime.now()

    return user_contexts[token]

def set_user_context_field(token: str, field: str, value):
    """Set a specific field in the user's context.

    Args:
        token: The user token
        field: The context field to update (e.g., 'destination', 'days', 'preferences', 'itinerary', 'trip_id')
        value: The new value
    """
    context_update = {field: value}
    return update_user_context(token, context=context_update)

def clear_user_context(token: str):
    """Clear the user context for a given token (reset to initial state).

    Args:
        token: The user token
    """
    if token in user_contexts:
        created_at = user_contexts[token].get("created_at", datetime.now())
        user_contexts[token] = {
            "destination": None,
            "days": None,
            "preferences": None,
            "itinerary": None,
            "trip_id": None,
            "created_at": created_at,
            "updated_at": datetime.now()
        }

    return user_contexts.get(token)

def delete_user_context(token: str):
    """Completely delete the user context for a given token.

    Args:
        token: The user token
    """
    if token in user_contexts:
        del user_contexts[token]

def get_all_users() -> Dict[str, Dict]:
    """Get all user contexts (for debugging/admin purposes).

    Returns:
        Dictionary of all user contexts
    """
    return user_contexts
