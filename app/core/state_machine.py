from enum import Enum
from app.services.llm_client import llm_client
from app.services.node_client import node_client
from app.services.vector_store import vector_store
import json

class ChatState(Enum):
    INIT = "INIT"
    NEED_DETAILS = "NEED_DETAILS" # Destination or Days missing
    CHECK_PREFS = "CHECK_PREFS"
    CONFIRM_PREFS = "CONFIRM_PREFS"
    UPDATING_PREFS = "UPDATING_PREFS"
    GENERATING = "GENERATING"
    REVIEW_ITINERARY = "REVIEW_ITINERARY" # Itinerary shown, waiting for save/edit
    EDITING = "EDITING"
    SAVED = "SAVED"

class ChatStateMachine:
    def __init__(self, token: str):
        self.token = token
        self.state = ChatState.INIT
        self.context = {
            "destination": None,
            "days": None,
            "preferences": None,
            "itinerary": None,
            "trip_id": None
        }

    async def handle_message(self, message: str):
        """
        Process incoming user message based on current state.
        Returns a generator that yields response chunks (strings) or dicts for special actions.
        """
        
        # 1. INIT / NEED_DETAILS: Extract Intent
        if self.state in [ChatState.INIT, ChatState.NEED_DETAILS]:
            msg_lower = message.lower().strip()
            
            # Fast Greeting (No LLM)
            if msg_lower in ["hi", "hello", "hey", "hola", "namaste"]:
                yield "Hi there! Where are you planning to go?"
                self.state = ChatState.NEED_DETAILS
                return

            # Use LLM to extract details
            extraction_prompt = f"""
            Extract the 'destination' and 'days' (number of days) from this user message: "{message}".
            If context exists, merge it.
            Current Context: Destination={self.context['destination']}, Days={self.context['days']}
            
            Output JSON: {{"destination": "string or null", "days": "int or null", "intent": "plan_trip"}}
            """
            print(f"DEBUG: Calling LLM for extraction. State: {self.state}")
            data = await llm_client.generate_json(extraction_prompt)
            print(f"DEBUG: Extraction Data: {data}")
            
            if data:
                if data.get("destination"): self.context["destination"] = data["destination"]
                if data.get("days"): self.context["days"] = data["days"]
            else:
                # Fallback: If LLM fails, assume the message IS the destination if it's short
                if len(message.split()) < 5:
                    print(f"DEBUG: LLM failed, using raw message as destination: {message}")
                    self.context["destination"] = message.strip()

            if not self.context["destination"]:
                self.state = ChatState.NEED_DETAILS
                yield "Where would you like to go?"
                return
            
            if not self.context["days"]:
                self.state = ChatState.NEED_DETAILS
                yield f"How many days are you planning for {self.context['destination']}?"
                return

            # If we have both, move to PREFS
            self.state = ChatState.CHECK_PREFS
            # Fallthrough to CHECK_PREFS logic immediately
        
        # 2. CHECK_PREFS: Fetch from Node
        if self.state == ChatState.CHECK_PREFS:
            prefs = await node_client.get_preferences(self.token)
            self.context["preferences"] = prefs
            
            if prefs and prefs.get("preferences"):
                 # Format preferences nicely for the user
                 p = prefs.get('preferences')
                 formatted_prefs = ", ".join([f"{k}: {v}" for k, v in p.items() if v])
                 self.state = ChatState.CONFIRM_PREFS
                 yield f"I found your saved preferences ({formatted_prefs}). Should I use these? (Yes/No/Update)"
                 return
            else:
                 self.state = ChatState.UPDATING_PREFS
                 yield "I don't see any saved preferences. Tell me about your travel style (e.g., Budget, Interests, Family/Solo)."
                 return

        # 3. CONFIRM_PREFS
        if self.state == ChatState.CONFIRM_PREFS:
            if "yes" in message.lower():
                self.state = ChatState.GENERATING
                # Fallthrough
            elif "update" in message.lower() or "no" in message.lower():
                self.state = ChatState.UPDATING_PREFS
                yield "Okay, what are your preferences for this trip?"
                return
            else:
                yield "Please say 'Yes' to use saved preferences or 'Update' to change them."
                return

        # 4. UPDATING_PREFS
        if self.state == ChatState.UPDATING_PREFS:
            # Simple update for now - take the whole message as prefs description
            # In real app, might want structured extraction again
            new_prefs = {"raw_text": message} # Simplified
            # Call Node to update
            await node_client.update_preferences(self.token, {"preferences": new_prefs})
            self.context["preferences"] = {"preferences": new_prefs}
            yield "Preferences updated!"
            self.state = ChatState.GENERATING
            # Fallthrough



        # 5. GENERATING
        if self.state == ChatState.GENERATING:
            yield "Checking my travel database...\n"
            
            # RAG: Search Vector DB
            dest_name = self.context['destination']
            # vector_store.search now returns a list of dicts with 'text', 'destination', 'distance'
            results = vector_store.search(dest_name, top_k=3)
            
            # Filter results for the specific destination
            relevant_texts = []
            for res in results:
                # Check if destination matches (loose check)
                if res.get('destination') and dest_name.lower() in res['destination'].lower():
                    relevant_texts.append(res['text'])
            
            # If no direct match, maybe use the top result if it's close enough or just use general knowledge?
            # For now, let's be strict but allow fallback if list is empty but we want to proceed with LLM knowledge
            if not relevant_texts:
                print(f"DEBUG: No RAG context found for {dest_name}. Proceeding with LLM knowledge only.")
                # yield f"I currently don't have specific data for {dest_name}, but I'll do my best!"
                # Don't return, just proceed with empty context
            
            yield "Found great spots! Generating your itinerary...\n"
            
            context_str = "\n\n".join(relevant_texts)
            
            prompt = f"""
            Plan a {self.context['days']}-day trip to {self.context['destination']}.
            Preferences: {self.context['preferences']}
            
            Use the following retrieved information to plan the trip:
            {context_str}
            
            Output a JSON structure EXACTLY like this:
            {{
              "title": "Trip Title (e.g., 'Royal Rajasthan Tour')",
              "date": "Dates not set", 
              "type": "Budget Category (e.g., 'Moderate', 'Luxury')",
              "focus": "Trip Focus (e.g., 'Heritage & Culture')",
              "days": [
                {{
                  "title": "Day 1: Arrival & Sightseeing",
                  "activities": ["Activity 1", "Activity 2", "Activity 3"]
                }}
              ]
            }}
            IMPORTANT: 
            1. 'days' must be an array. 'activities' must be an array of strings.
            2. Do NOT invent specific calendar dates (like Oct 26) unless the user explicitly provided a start date in the preferences. Use generic 'Day 1', 'Day 2' etc.
            3. Set "date" field to "Dates not set" unless user specified dates.
            """
            
            itinerary_json = await llm_client.generate_json(prompt)
            self.context["itinerary"] = itinerary_json
            
            # Stream the formatted itinerary to user
            yield json.dumps({"type": "itinerary", "data": itinerary_json}) 
            
            self.state = ChatState.REVIEW_ITINERARY
            yield "Do you want to save this trip? (Yes/No)"
            return

        # 6. REVIEW_ITINERARY
        if self.state == ChatState.REVIEW_ITINERARY:
            msg_lower = message.lower()
            if "yes" in msg_lower or "save" in msg_lower:
                # Save to Node
                # Fix: Map LLM output keys to MongoDB Schema keys
                itinerary_data = self.context["itinerary"]
                
                # Map 'days' array from LLM to 'itinerary' array for Schema
                # Schema expects: [{ day: Number, title: String, activities: [String] }]
                mapped_itinerary = []
                if itinerary_data.get("days"):
                    for idx, day_obj in enumerate(itinerary_data["days"]):
                        mapped_itinerary.append({
                            "day": idx + 1,
                            "title": day_obj.get("title", f"Day {idx+1}"),
                            "activities": day_obj.get("activities", [])
                        })

                trip_payload = {
                    "tripName": itinerary_data.get("title", f"Trip to {self.context['destination']}"),
                    "destination": self.context["destination"],
                    "days": self.context["days"],
                    "tripType": itinerary_data.get("type"),
                    "itinerary": mapped_itinerary,
                    "preferencesSnapshot": self.context["preferences"]
                }
                
                res = await node_client.create_trip(self.token, trip_payload)
                if res and res.get("success"):
                    self.context["trip_id"] = res.get("trip", {}).get("_id") # Node returns { success: true, trip: {...} }
                    self.state = ChatState.SAVED
                    yield "Trip saved successfully!"
                elif res and res.get("error"):
                    yield f"Failed to save trip: {res['error']}"
                else:
                    yield "Failed to save trip. Please try again."
            
            elif "update" in msg_lower or "change" in msg_lower or "edit" in msg_lower:
                self.state = ChatState.EDITING
                yield "Okay, what would you like to change? (e.g., 'Make it 5 days', 'Add more nature')"
                return
            else:
                yield "Please say 'Save' to save this trip, or 'Update' to make changes."
                return

        # 7. EDITING
        if self.state == ChatState.EDITING:
            # Use LLM to interpret the change request
            change_prompt = f"""
            Current Trip Context:
            Destination: {self.context['destination']}
            Days: {self.context['days']}
            Preferences: {self.context['preferences']}
            
            User Change Request: "{message}"
            
            Update the context based on the request.
            Output JSON: {{"destination": "string (keep current if no change)", "days": "int (keep current if no change)", "new_preferences": "string (additional prefs)"}}
            """
            
            changes = await llm_client.generate_json(change_prompt)
            
            if changes:
                if changes.get("destination"): self.context["destination"] = changes["destination"]
                if changes.get("days"): self.context["days"] = changes["days"]
                if changes.get("new_preferences"):
                    # Append new prefs to existing
                    current_prefs = self.context["preferences"]
                    if isinstance(current_prefs, dict):
                        # If it's a dict, maybe add to a 'notes' field or 'raw_text'
                        current_prefs["updates"] = changes["new_preferences"]
                    else:
                        self.context["preferences"] = str(current_prefs) + ", " + changes["new_preferences"]

            self.state = ChatState.GENERATING
            yield f"Got it. Updating your trip to {self.context['destination']} for {self.context['days']} days..."
            # Fallthrough to GENERATING to re-create itinerary

        # 8. SAVED
        if self.state == ChatState.SAVED:
            yield "Trip is saved. You can ask to 'delete' it or plan a 'new' trip."
            if "delete" in message.lower():
                if self.context["trip_id"]:
                    await node_client.delete_trip(self.token, self.context["trip_id"])
                    yield "Trip deleted."
                    self.state = ChatState.INIT
                    self.context = {}
            elif "new" in message.lower():
                self.state = ChatState.INIT
                self.context = {}
                yield "Ready for a new adventure! Where to?"
