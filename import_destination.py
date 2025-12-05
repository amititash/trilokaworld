import os
import sys
import re
import pymongo
import subprocess
from dotenv import load_dotenv

load_dotenv()

# Config
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
DB_NAME = "ai_travel"

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
    if len(sys.argv) < 3:
        print("Usage: python3 import_destination.py <state> <destination>")
        print("Example: python3 import_destination.py himachal kasol")
        return

    state = sys.argv[1]
    destination_name = sys.argv[2]
    
    base_path = os.path.join("data", state, destination_name)
    txt_file_path = os.path.join(base_path, f"{destination_name}.txt")
    img_file_path = os.path.join(base_path, "img.txt")

    if not os.path.exists(txt_file_path):
        print(f"Error: Data file '{txt_file_path}' not found.")
        return

    print(f"Reading {txt_file_path}...")
    with open(txt_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    image_url = ""
    if os.path.exists(img_file_path):
        print(f"Reading image URL from {img_file_path}...")
        with open(img_file_path, 'r', encoding='utf-8') as f:
            image_url = f.read().strip()
    else:
        print(f"Warning: Image file '{img_file_path}' not found. No image will be added.")

    # Infer name from destination argument
    name = destination_name.replace("_", " ").title()

    print(f"Parsing content for '{name}'...")
    details = parse_file_content(content)

    # Connect to Mongo
    client_mongo = pymongo.MongoClient(MONGO_URI)
    db = client_mongo[DB_NAME]
    destinations_col = db["destinations"]

    # 1. Location
    location = f"{state.title()}, India" # Default fallback
    if "LOCATION" in details:
        location = details["LOCATION"].split("\n")[0].strip()

    # 2. Description (Try to make it a list of attractions like other cards)
    description = ""
    if "attractions" in details:
        # Try to extract attraction names from the start of paragraphs
        attraction_names = []
        paragraphs = details["attractions"].split("\n")
        for p in paragraphs:
            p = p.strip()
            if not p: continue
            # Heuristic: "Name is..." or "Name are..."
            # Regex to capture text before " is " or " are "
            match = re.match(r"^(.*?)(?:\s+is\s+|\s+are\s+)", p)
            if match:
                name_candidate = match.group(1)
                # Filter out long sentences or "The" if it's just "The"
                if len(name_candidate) < 50: 
                    attraction_names.append(name_candidate)
        
        if attraction_names:
            description = ", ".join(attraction_names[:4]) + "."
        else:
            # Fallback to first 150 chars of attractions
            description = details["attractions"][:150] + "..."
    else:
        # Fallback to history
        description = details.get("history", "")[:150] + "..."

    # 3. Badge
    badge = "Popular"
    full_text = " ".join(details.values()).lower()
    if "hill station" in full_text:
        badge = "Hill Station"
    elif "spiritual" in full_text or "temple" in full_text:
        badge = "Spiritual"
    elif "wildlife" in full_text or "sanctuary" in full_text:
        badge = "Wildlife"

    # Construct Document
    doc = {
        "name": name,
        "location": location,
        "description": description,
        "emoji": "📍",
        "images": [image_url] if image_url else [],
        "details": details,
        "rating": 4.5,
        "gradient": "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
        "badge": badge,
        "categories": ["mountain", "nature"] if "hill station" in full_text else ["heritage"] # Simple category logic
    }

    # Upsert
    result = destinations_col.update_one(
        {"name": name},
        {"$set": doc},
        upsert=True
    )

    if result.upserted_id:
        print(f"Successfully IMPORTED '{name}' to MongoDB!")
    else:
        print(f"Successfully UPDATED '{name}' in MongoDB!")

    print("Starting sync to ChromaDB...")
    try:
        subprocess.run(["python3", "sync_mongo_to_chroma.py"], check=True)
        print("Sync completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error during sync: {e}")

if __name__ == "__main__":
    import_destination()
