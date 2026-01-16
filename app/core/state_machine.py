from enum import Enum
from app.services.llm_client import llm_client
from app.services.node_client import node_client
from app.services.vector_store import vector_store
import json
from user_manager import get_user_context, set_user_context_field

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
				print(f"DEBUG: No RAG context found for {dest_name}. Checking backend database...")
				
				# Fallback: Check if destination exists in the main database
				all_destinations = await node_client.get_destinations(self.token)
				
				found_in_db = False
				if isinstance(all_destinations, list):
					for d in all_destinations:
						if d.get("name") and dest_name.lower() in d.get("name").lower():
							found_in_db = True
							break
				
				if found_in_db:
					print(f"DEBUG: Found {dest_name} in backend DB. Proceeding with LLM knowledge.")
					# Proceed with empty relevant_texts (LLM will use its own knowledge)
				else:
					print(f"DEBUG: {dest_name} not found in backend DB either. Stopping.")
					yield f"I'm sorry, I don't have information about {dest_name} in my database."
					self.state = ChatState.INIT
					return
			
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
			
			if not itinerary_json:
				yield "I'm sorry, I couldn't generate the itinerary at this moment. Please try again or provide more details."
				return

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


from fastapi import WebSocket
from chat_manager import get_messages, add_message
from portkey_ai import AsyncPortkey
from app.core.config import settings

async_portkey = AsyncPortkey(
	api_key=settings.PORT_KEY_API_KEY,
	config=settings.PORT_KEY_ID
)

async def process_messages(websocket: WebSocket, token: int):
	message_arr = [{"role" : "system","content" : f"""
				 
	You are Triloka, a friendly and helpful travel agent AI assistant. Your role is to help users prepare travel itineraries and identify what action they want to take with their itinerary.

	Your task is to:
	1. Analyze the user's request to understand what they need
	2. Provide helpful travel planning assistance based on their needs

	Before responding, think through:
	- What is the user asking for? 
	- What action type is this? 
	- What travel details have they provided? (destination, dates, preferences, etc.)
	- What additional information or suggestions would be helpful?

	After your analysis, provide your response in the following format:

	Provide your helpful response as Triloka. This should include:
	- A warm greeting acknowledging their request
	- The travel itinerary assistance they need (destinations, activities, accommodations, transportation, etc.)
	- Any clarifying questions if you need more information
	- Confirmation of what action you understand them to want (save/update/delete)
	- Helpful suggestions or recommendations based on their travel plans

	Guidelines:
	- Be warm, friendly, and professional in your tone
	- If the user mentions wanting to "save" their itinerary
	- If they want to "update," "modify," "change," or "edit" an existing itinerary
	- If they want to "delete" or "remove" an itinerary
	- If they're starting fresh with travel planning
	- Provide practical travel advice including suggested activities, timing, and logistics
	- If the request is unclear, ask clarifying questions
	- Do not confirm your understanding of what action they want to take
	- Do not be verbose about your tasks	 
	"""}]
	message_arr.extend(get_messages(token=token,k=10))
	response_text = ""
	function_name = ""
	function_args = ""

	functions = [
		{
			"name": "plan_destination_trip",
			"description": "Plans a travel itinerary for a specified destination and duration",
			"parameters": {
				"type": "object",
				"properties": {
				"destination": {
					"type": "string",
					"description": "The city, region, state, or country where the user wants to travel"
				},
				"days": {
					"type": "integer",
					"description": "Number of days the user is planning to travel"
				}
				},
				"required": [
					"destination",
					"days"
				],
			}
		},
		{
			"name": "crud_itinerary",
			"description": "Perform CRUD operations (update, modify, delete) on the itinerary",
			"parameters": {
				"type": "object",
				"properties": {
				"operation_type": {
					"type": "string",
					"description": "Type of operation to perform on the itinerary",
					"enum": [
						"save",
						"update",
						"modify",
						"delete"
					]
				},
				},
				},
				"required": [
					"operation_type",
					"location",
					"itinerary_name"
				],
			}
	]

	try:
		response = await async_portkey.with_options(
			metadata={
				"user_id": "function",
			}
		).chat.completions.create(
			messages=message_arr,
			stream=True,
			functions=functions,
		)
		async for res in response:
			delta = res.choices[0].delta
			if hasattr(delta, 'function_call') or 'function_call' in delta.model_dump():
				function_call = delta.function_call or delta.model_dump().get('function_call')
				
				if function_call:
					if hasattr(function_call, 'name') or 'name' in function_call:
						function_name = function_call.name if hasattr(function_call, 'name') else function_call['name']
					
					if hasattr(function_call, 'arguments') or 'arguments' in function_call:
						function_args += function_call.arguments if hasattr(function_call, 'arguments') else function_call['arguments']

			if res.choices[0].finish_reason == "function_call":
				function_full_message = {
					"message": {
						"function_call": {
							"name": function_name,
							"arguments": function_args,
						}
					}
				}
				print(function_full_message)
				if function_name.strip() == "plan_destination_trip":

					prefs = await node_client.get_preferences(token)

					formatted_prefs = ", ".join([f"{k}: {v}" for k, v in prefs.get("data").items() if v])

					# Parse function_args from JSON string to dict
					parsed_args = json.loads(function_args)
					destination = parsed_args.get("destination")


					days = parsed_args.get("days")
					results = vector_store.search(destination, top_k=3)
					# Filter results for the specific destination
					relevant_texts = []
					for res in results:
						# Check if destination matches (loose check)
						# if res.get('destination') and destination.lower() in res['destination'].lower():
						relevant_texts.append(res['text'])

					context_str = "\n\n".join(relevant_texts)

					prompt = f"""
					Plan a {days}-day trip to {destination}.
					Preferences: {formatted_prefs}

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
					response = await async_portkey.with_options(
						metadata={
							"user_id": "small",
						}
					).chat.completions.create(
						messages=[
							{"role": "user", "content": prompt}
						],
						temperature=0.3,
						top_p=0.6,
						response_format={
							"type": "json_schema",
                			"json_schema":{
							"name": "trip_plan",
							"schema": {
								"type": "object",
								"properties": {
								"title": {
									"type": "string",
									"description": "Trip Title (e.g., 'Royal Rajasthan Tour')",
									"minLength": 1
								},
								"date": {
									"type": "string",
									"description": "Dates of the trip, or 'Dates not set' if unspecified",
									"minLength": 1
								},
								"type": {
									"type": "string",
									"description": "Budget Category (e.g., 'Moderate', 'Luxury')",
									"minLength": 1
								},
								"focus": {
									"type": "string",
									"description": "Trip Focus (e.g., 'Heritage & Culture')",
									"minLength": 1
								},
								"days": {
									"type": "array",
									"description": "List of trip days with titles and activities",
									"items": {
									"type": "object",
									"properties": {
										"title": {
										"type": "string",
										"description": "Title for this day (e.g., 'Day 1: Arrival & Sightseeing')",
										"minLength": 1
										},
										"activities": {
										"type": "array",
										"description": "List of activity descriptions for this day",
										"items": {
											"type": "string",
											"minLength": 1
										}
										}
									},
									"required": [
										"title",
										"activities"
									],
									}
								}
								},
								"required": [
								"title",
								"date",
								"type",
								"focus",
								"days"
								],
							},
						}}
					)
					response_json = json.loads(response.choices[0].message.content)

					yield json.dumps({"type": "itinerary", "data": response_json})
					add_message(token=token,message=response.choices[0].message.content,role="system")
					set_user_context_field(token=token,field="itinerary",value=response_json)
					set_user_context_field(token=token,field="destination",value=destination)
					set_user_context_field(token=token,field="days",value=days)

				elif function_name.strip() == "crud_itinerary":
					itinerary_data = get_user_context(token=token)
					# Map 'days' array from LLM to 'itinerary' array for Schema
					# Schema expects: [{ day: Number, title: String, activities: [String] }]
					mapped_itinerary = []
					if itinerary_data.get("itinerary",{}).get("days",{}):
						for idx, day_obj in enumerate(itinerary_data["itinerary"]["days"]):
							mapped_itinerary.append({
								"day": idx + 1,
								"title": day_obj.get("title", f"Day {idx+1}"),
								"activities": day_obj.get("activities", [])
							})

					trip_payload = {
						"tripName": itinerary_data.get("itinerary", {}).get("title", itinerary_data.get('destination','Delhi')),
						"destination": itinerary_data.get("destination",'Delhi'),
						"days": itinerary_data.get("days"),
						"tripType": itinerary_data.get("itinerary", {}).get("type"),
						"itinerary": mapped_itinerary,
						"preferencesSnapshot": itinerary_data.get("preferences")
					}
					res = await node_client.create_trip(token, trip_payload)
					if res and res.get("success"):
						# self.context["trip_id"] = res.get("trip", {}).get("_id") # Node returns { success
						set_user_context_field(token=token,field="trip_id",value=res.get("trip", {}).get("_id"))
						yield "Successfully saved your itinerary!"
						add_message(token=token,message="Successfully saved your itinerary!",role="system")
					else:
						error_msg = res.get("error", "Unknown error") if res else "Failed to save trip"
						yield f"Failed to save itinerary: {error_msg}"
						add_message(token=token,message=f"Failed to save itinerary: {error_msg}",role="system")
			elif res.choices[0].delta.content:
				response_text += res.choices[0].delta.content
				
		
		if response_text != "":
			yield response_text
			add_message(token=token,message=response_text,role="system")

	except Exception as e:
		pass

