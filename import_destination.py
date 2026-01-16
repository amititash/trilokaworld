import os
import re
import pymongo
from dotenv import load_dotenv

load_dotenv()

# Config
MONGO_URI = "mongodb+srv://mihir:adaptiv@cluster0.vgaf45a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "ai_travel"

PORT_KEY_API_KEY="NIy2lYZ8SVKOLs3BHK+Jc4h2b3ol"
PORT_KEY_ID="pc-trilok-3b6d0f"

def parse_file_content(content):
    sections = {}
    lines = content.split("\n")
    current_section = None
    section_content = []

    for line in lines:
        trimmed = line.strip()
        if not trimmed: continue

        # Check if line is a section header (all caps, short)
        if trimmed == trimmed.upper() and len(trimmed) < 50 and "HTTP" not in trimmed:
            if current_section:
                sections[current_section] = "\n".join(section_content).strip()
            
            # Normalize section name
            raw_sec = trimmed.lower().replace(" ", "")
            if "history" in raw_sec: current_section = "history"
            elif "besttime" in raw_sec: current_section = "bestTime"
            elif "weather" in raw_sec: current_section = "weather"
            elif "attractions" in raw_sec: current_section = "attractions"
            elif "family" in raw_sec: current_section = "forFamily"
            elif "couples" in raw_sec: current_section = "forCouples"
            elif "solo" in raw_sec: current_section = "forSolo"
            elif "adventure" in raw_sec: current_section = "forAdventure"
            elif "culture" in raw_sec: current_section = "culture"
            elif "food" in raw_sec: current_section = "food"
            else: current_section = raw_sec # Fallback
            
            section_content = []
        else:
            section_content.append(trimmed)

    if current_section:
        sections[current_section] = "\n".join(section_content).strip()

    return sections

def import_destination():
    data_folder = "data"

    if not os.path.exists(data_folder):
        print(f"Error: Data folder '{data_folder}' not found.")
        return

    # Get all folders inside data folder
    city_folders = [f for f in os.listdir(data_folder) if os.path.isdir(os.path.join(data_folder, f))]

    if not city_folders:
        print(f"No folders found in '{data_folder}'")
        return

    print(f"Found {len(city_folders)} cities to import...")
    from portkey_ai import Portkey
    portkey = Portkey(
        api_key=PORT_KEY_API_KEY,
        config=PORT_KEY_ID
    )
    for destination_name in city_folders:
        print(f"\n{'='*50}")
        print(f"Processing: {destination_name}")
        print(f"{'='*50}")

        base_path = os.path.join(data_folder, destination_name)
        txt_file_path = os.path.join(base_path, f"{destination_name}.txt")
        img_file_path = os.path.join(base_path, "img.txt")

        # Load content from files into variables
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            destination_content = f.read()

        image_url = ""
        if os.path.exists(img_file_path):
            with open(img_file_path, 'r', encoding='utf-8') as f:
                image_url = f.read().strip()

        prompt = f"""
        You will be converting raw text input about a travel destination (specifically related to Dharamshala or similar destinations) into a structured JSON format. 

        Here is the raw text you need to process:

        <raw_text>
        {destination_content}
        </raw_text>

        Your task is to carefully read through this raw text and extract relevant information to populate a JSON object according to the schema provided below.

        The JSON output must conform to this exact schema:

        ```json
        {{
        "name": "string - Name of the place",
        "badge": "string - Primary badge/category label (e.g., 'Spiritual Hub', 'Adventure Destination', 'Cultural Site')",
        "categories": ["array of strings - Categories describing the place"],
        "description": "string - Brief description or highlights (2-3 sentences)",
        "details": {{
            "dharamshalatravelguide": "string - Extended travel guide information or general overview",
            "history": "string - Complete historical background",
            "bestTime": "string - Best times and advice for visiting",
            "weather": "string - Overview of weather and climate",
            "attractions": "string - Major attractions and highlights",
            "forFamily": "string - Advice and appeal for families",
            "forCouples": "string - Considerations and appeal for couples",
            "forSolo": "string - Information for solo travelers",
            "forAdventure": "string - Adventure/trekking activities and advice",
            "forvloggersandphotographers": "string - Opportunities and advice for content creators"
        }},
        "emoji": "string - Single emoji representing the place (1-2 characters)",
        "gradient": "string - CSS gradient string for UI coloring (e.g., 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')",
        "images": ["array of strings - Image URLs if mentioned, otherwise empty array"],
        "location": "string - City/region and country (e.g., 'Dharamshala, India')",
        "rating": number - Overall rating between 0 and 5
        }}

        Guidelines for extracting and formatting information:

        1. **name**: Extract the primary name of the destination from the text
        2. **badge**: Determine the most appropriate primary category (e.g., "Spiritual Retreat", "Mountain Town", "Cultural Hub")
        3. **categories**: List 3-5 relevant categories based on what the text describes
        4. **description**: Create a concise 2-3 sentence summary of the key highlights
        5. **details object**: Extract or infer information for each field:
        - If specific information isn't provided for a field, write a reasonable inference based on the overall context
        - Each field should contain at least 2-3 sentences of relevant information
        - Be comprehensive but concise
        6. **emoji**: Choose one emoji that best represents the destination
        7. **gradient**: Create an appropriate CSS gradient string that matches the mood/theme of the destination
        8. **images**: Extract any URLs mentioned; if none, use an empty array []
        9. **location**: Format as "City/Region, Country"
        10. **rating**: Infer a rating from 0-5 based on how the destination is described (positive descriptions = higher rating)

        Important formatting requirements:
        - Output must be valid JSON
        - Properly escape all quotes and special characters within strings
        - Use double quotes for all JSON keys and string values
        - Ensure all required fields are present
        - Do not include any text outside the JSON structure in your final answer

        Before generating the JSON, use a scratchpad to:
        1. Identify key information in the raw text
        2. Map information to the appropriate JSON fields
        3. Note any missing information that needs to be inferred
        4. Plan your emoji, gradient, and rating choices


        Your output should include valid json only. Do not be verbose.
        """
        response = portkey.with_options(
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
                    "name": "dharamshala_destination",
                    "schema": {
                        "type": "object",
                        "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the place."
                        },
                        "badge": {
                            "type": "string",
                            "description": "Primary badge/category label of the place."
                        },
                        "categories": {
                            "type": "array",
                            "description": "List of categories describing the place.",
                            "items": {
                            "type": "string"
                            }
                        },
                        "description": {
                            "type": "string",
                            "description": "Brief description or highlights."
                        },
                        "details": {
                            "type": "object",
                            "properties": {
                            "dharamshalatravelguide": {
                                "type": "string",
                                "description": "Extended travel guide or link."
                            },
                            "history": {
                                "type": "string",
                                "description": "Complete historical background."
                            },
                            "bestTime": {
                                "type": "string",
                                "description": "Best times and advice for visiting."
                            },
                            "weather": {
                                "type": "string",
                                "description": "Overview of weather and climate."
                            },
                            "attractions": {
                                "type": "string",
                                "description": "Major attractions and highlights."
                            },
                            "forFamily": {
                                "type": "string",
                                "description": "Advice and appeal for families."
                            },
                            "forCouples": {
                                "type": "string",
                                "description": "Considerations and appeal for couples."
                            },
                            "forSolo": {
                                "type": "string",
                                "description": "Information for solo travelers."
                            },
                            "forAdventure": {
                                "type": "string",
                                "description": "Adventure/trekking activities and advice."
                            },
                            "forvloggersandphotographers": {
                                "type": "string",
                                "description": "Opportunities and advice for content creators."
                            }
                            },
                            "required": [
                            "dharamshalatravelguide",
                            "history",
                            "bestTime",
                            "weather",
                            "attractions",
                            "forFamily",
                            "forCouples",
                            "forSolo",
                            "forAdventure",
                            "forvloggersandphotographers"
                            ],
                            "description": "Nested object detailing various dimensions of Dharamshala."
                        },
                        "emoji": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 2,
                            "description": "Emoji representing the place."
                        },
                        "gradient": {
                            "type": "string",
                            "description": "CSS gradient string for UI coloring."
                        },
                        "images": {
                            "type": "array",
                            "description": "Image URLs representing the place.",
                            "items": {
                            "type": "string"
                            }
                        },
                        "location": {
                            "type": "string",
                            "description": "City/region and country."
                        },
                        "rating": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 5,
                            "description": "Overall rating of the place."
                        }
                        },
                        "required": [
                        "name",
                        "badge",
                        "categories",
                        "description",
                        "details",
                        "emoji",
                        "gradient",
                        "images",
                        "location",
                        "rating"
                        ],
                    },
                    }}
        )
        import json
        response_json = json.loads(response.choices[0].message.content)
        response_json["images"] = [image_url]
        client_mongo = pymongo.MongoClient(MONGO_URI)
        db = client_mongo[DB_NAME]
        destinations_col = db["destinations"]
        result = destinations_col.update_one(
            {"name": response_json['name']},
            {"$set": response_json},
            upsert=True
        )

        # if not os.path.exists(txt_file_path):
        #     print(f"Error: Data file '{txt_file_path}' not found. Skipping...")
        #     continue

        # print(f"Reading {txt_file_path}...")
        # with open(txt_file_path, 'r', encoding='utf-8') as f:
        #     content = f.read()

        # image_url = ""
        # if os.path.exists(img_file_path):
        #     print(f"Reading image URL from {img_file_path}...")
        #     with open(img_file_path, 'r', encoding='utf-8') as f:
        #         image_url = f.read().strip()
        # else:
        #     print(f"Warning: Image file '{img_file_path}' not found. No image will be added.")

        # # Infer name from destination argument
        # name = destination_name.replace("_", " ").replace("-", " ").title()

        # print(f"Parsing content for '{name}'...")
        # details = parse_file_content(content)

        # # Connect to Mongo
        # client_mongo = pymongo.MongoClient(MONGO_URI)
        # db = client_mongo[DB_NAME]
        # destinations_col = db["destinations"]

        # # 1. Location
        # location = "India"  # Default fallback
        # if "LOCATION" in details:
        #     location = details["LOCATION"].split("\n")[0].strip()

        # # 2. Description (Try to make it a list of attractions like other cards)
        # description = ""
        # if "attractions" in details:
        #     # Try to extract attraction names from the start of paragraphs
        #     attraction_names = []
        #     paragraphs = details["attractions"].split("\n")
        #     for p in paragraphs:
        #         p = p.strip()
        #         if not p: continue
        #         # Heuristic: "Name is..." or "Name are..."
        #         # Regex to capture text before " is " or " are "
        #         match = re.match(r"^(.*?)(?:\s+is\s+|\s+are\s+)", p)
        #         if match:
        #             name_candidate = match.group(1)
        #             # Filter out long sentences or "The" if it's just "The"
        #             if len(name_candidate) < 50:
        #                 attraction_names.append(name_candidate)

        #     if attraction_names:
        #         description = ", ".join(attraction_names[:4]) + "."
        #     else:
        #         # Fallback to first 150 chars of attractions
        #         description = details["attractions"][:150] + "..."
        # else:
        #     # Fallback to history
        #     description = details.get("history", "")[:150] + "..."

        # # 3. Badge
        # badge = "Popular"
        # full_text = " ".join(details.values()).lower()
        # if "hill station" in full_text:
        #     badge = "Hill Station"
        # elif "spiritual" in full_text or "temple" in full_text:
        #     badge = "Spiritual"
        # elif "wildlife" in full_text or "sanctuary" in full_text:
        #     badge = "Wildlife"

        # Construct Document
        # doc = {
        #     "name": name,
        #     "location": location,
        #     "description": description,
        #     "emoji": "📍",
        #     "images": [image_url] if image_url else [],
        #     "details": details,
        #     "rating": 4.5,
        #     "gradient": "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
        #     "badge": badge,
        #     "categories": ["mountain", "nature"] if "hill station" in full_text else ["heritage"] # Simple category logic
        # }

        # Upsert
    #     result = destinations_col.update_one(
    #         {"name": name},
    #         {"$set": doc},
    #         upsert=True
    #     )

    #     if result.upserted_id:
    #         print(f"Successfully IMPORTED '{name}' to MongoDB!")
    #     else:
    #         print(f"Successfully UPDATED '{name}' in MongoDB!")

    # print("\nAll cities processed!")
    # print("Starting sync to ChromaDB...")
    # try:
    #     subprocess.run(["python3", "sync_mongo_to_chroma.py"], check=True)
    #     print("Sync completed successfully!")
    # except subprocess.CalledProcessError as e:
    #     print(f"Error during sync: {e}")

# if __name__ == "__main__":
#     import_destination()
