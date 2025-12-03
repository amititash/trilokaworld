import httpx
from app.core.config import settings

class NodeClient:
    def __init__(self):
        self.base_url = settings.NODE_API_URL

    async def _request(self, method: str, endpoint: str, token: str, json: dict = None):
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, f"{self.base_url}{endpoint}", headers=headers, json=json)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"Node API Error: {e.response.text}")
                return {"error": f"Node API Error: {e.response.text}"}
            except Exception as e:
                print(f"Node Client Error: {e}")
                return {"error": f"Node Client Error: {str(e)}"}

    async def get_preferences(self, token: str):
        return await self._request("GET", "/user/preferences", token)

    async def update_preferences(self, token: str, preferences: dict):
        # Assuming PUT /user/preferences based on user request description
        # If the Node API uses POST, change to POST
        return await self._request("PUT", "/user/preferences", token, json=preferences)

    async def create_trip(self, token: str, trip_data: dict):
        return await self._request("POST", "/trip", token, json=trip_data)

    async def update_trip(self, token: str, trip_id: str, trip_data: dict):
        return await self._request("PUT", f"/trip/{trip_id}", token, json=trip_data)

    async def delete_trip(self, token: str, trip_id: str):
        return await self._request("DELETE", f"/trip/{trip_id}", token)

    async def get_destinations(self, token: str):
        # Fetch all destinations from the public API
        # Note: This endpoint might not require a token if it's public, but we pass it for consistency if needed.
        # Based on routes, /api/destinations is public.
        return await self._request("GET", "/api/destinations", token)

node_client = NodeClient()
