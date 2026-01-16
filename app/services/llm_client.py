import google.generativeai as genai
from openai import AsyncOpenAI
from app.core.config import settings
import json
import asyncio
from portkey_ai import AsyncPortkey

class LLMClient:
	def __init__(self):
		self.async_portkey = AsyncPortkey(
			api_key=settings.PORT_KEY_API_KEY,
			config=settings.PORT_KEY_ID
		)
		# self.provider = settings.MODEL_PROVIDER
		
		# if self.provider == "gemini":
		#     genai.configure(api_key=settings.GEMINI_API_KEY)
		#     # Using Gemini 2.0 Flash as requested
		#     self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
		# elif self.provider == "openai":
		#     self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

	async def generate_text_stream(self, prompt: str):
		"""
		Streams text response from the configured LLM provider.
		"""
		# if self.provider == "gemini":
		#     response = await self.gemini_model.generate_content_async(prompt, stream=True)
		#     async for chunk in response:
		#         if chunk.text:
		#             yield chunk.text
		
		# elif self.provider == "openai":
		#     stream = await self.openai_client.chat.completions.create(
		#         model="gpt-3.5-turbo", # Or gpt-4
		#         messages=[{"role": "user", "content": prompt}],
		#         stream=True,
		#     )
		#     async for chunk in stream:
		#         if chunk.choices[0].delta.content:
		#             yield chunk.choices[0].delta.content

		response = await self.async_portkey.with_options(
				metadata={
					"user_id" : "small",
				}
			).chat.completions.create(
			messages=[
				{
					"role": "system", 
					"content": prompt
				},
			],
			stream=True,
			temperature=0.3,
		)
		async for chunk in response:
			content = chunk.choices[0].delta.content
			yield content

	async def generate_json(self, prompt: str):
		"""
		Generates a JSON response (non-streaming) for structured data.
		"""
		# print(f"DEBUG: Generating JSON with provider {self.provider}")
		# Enforce JSON structure in prompt if not already present
		json_prompt = f"{prompt}\n\nIMPORTANT: Output ONLY valid JSON."

		response = await self.async_portkey.with_options(
			metadata={
				"user_id": "small",
			}
		).chat.completions.create(
			messages=[
				{"role": "user", "content": json_prompt}
			],
			temperature=0.3,
			top_p=0.6,
			# max_completion_tokens=2048,
			response_format={"type": "json_object"}
		)
		
		assistant_reply = response.choices[0].message.content
		return json.loads(assistant_reply)
		# if self.provider == "gemini":
		# 	try:
		# 		print("DEBUG: Calling Gemini API...")
		# 		response = await self.gemini_model.generate_content_async(json_prompt)
		# 		print(f"DEBUG: Gemini Response: {response.text}")
		# 		text = response.text
		# 		# Clean up potential markdown code blocks
		# 		text = text.replace("```json", "").replace("```", "").strip()
		# 		return json.loads(text)
		# 	except Exception as e:
		# 		print(f"ERROR in generate_json (Gemini): {e}")
		# 		import traceback
		# 		traceback.print_exc()
		# 		return None

		# elif self.provider == "openai":
		# 	response = await self.openai_client.chat.completions.create(
		# 		model="gpt-3.5-turbo",
		# 		messages=[{"role": "user", "content": json_prompt}],
		# 		response_format={"type": "json_object"}
		# 	)
		# 	try:
		# 		return json.loads(response.choices[0].message.content)
		# 	except json.JSONDecodeError:
		# 		 print(f"Failed to decode JSON from OpenAI: {response.choices[0].message.content}")
		# 		 return None

llm_client = LLMClient()
