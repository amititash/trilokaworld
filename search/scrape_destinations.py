import requests
import os

EXA_API_KEY = os.getenv("EXA_API_KEY")


def search_exa(query: str, k: int = 10):
    url = "https://api.exa.ai/search"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer f40b4ee2-e3e3-4dd2-8aef-cf455727fd53"
    }

    payload = {
        "query": query,
        "type": "keyword",
        "numResults": k,
        "contents": {
            "text": True,
            "images": {
                "count": 1
            },
        }
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    data = response.json()

    # Collect all text and one image
    all_text = []
    image_link = None

    if "results" in data:
        for result in data["results"]:
            # Collect text from each result
            if "text" in result:
                all_text.append(result["text"])

            # Get the first available image if we don't have one yet
            if not image_link:
                if "images" in result and len(result["images"]) > 0:
                    image_link = result["images"][0]
                elif "image" in result:
                    image_link = result["image"]

    return {
        "text": "\n\n---\n\n".join(all_text),
        "image": image_link
    }
    
def search_query():
    """Generate 100 search queries for 100 different places in India"""

    places_in_india = [
        "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
        "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat",
        "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane",
        "Bhopal", "Visakhapatnam", "Pimpri-Chinchwad", "Patna", "Vadodara",
        "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad",
        "Meerut", "Rajkot", "Kalyan-Dombivli", "Vasai-Virar", "Varanasi",
        "Srinagar", "Aurangabad", "Dhanbad", "Amritsar", "Navi Mumbai",
        "Allahabad", "Ranchi", "Howrah", "Coimbatore", "Jabalpur",
        "Gwalior", "Vijayawada", "Jodhpur", "Madurai", "Raipur",
        "Kota", "Chandigarh", "Guwahati", "Solapur", "Hubli-Dharwad",
        "Mysore", "Tiruchirappalli", "Bareilly", "Aligarh", "Tiruppur",
        "Moradabad", "Jalandhar", "Bhubaneswar", "Salem", "Warangal",
        "Mira-Bhayanagar", "Thiruvananthapuram", "Bhiwandi", "Saharanpur", "Guntur",
        "Amravati", "Bikaner", "Noida", "Jamshedpur", "Bhilai",
        "Cuttack", "Firozabad", "Kochi", "Nellore", "Bhavnagar",
        "Dehradun", "Durgapur", "Asansol", "Rourkela", "Nanded",
        "Kolhapur", "Ajmer", "Akola", "Gulbarga", "Jamnagar",
        "Ujjain", "Loni", "Siliguri", "Jhansi", "Ulhasnagar",
        "Jammu", "Sangli-Miraj", "Mangalore", "Erode", "Belgaum",
        "Ambattur", "Tirunelveli", "Malegaon", "Gaya", "Udaipur"
    ]

    queries = []
    for place in places_in_india:
        query = f"tourist attractions and places to visit in {place} India"
        queries.append(query)

    return queries
    


def main():
    import os

    # Create data folder if it doesn't exist
    data_folder = "data"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    queries = search_query()
    places_in_india = [
        "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
        "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat",
        "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane",
        "Bhopal", "Visakhapatnam", "Pimpri-Chinchwad", "Patna", "Vadodara",
        "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad",
        "Meerut", "Rajkot", "Kalyan-Dombivli", "Vasai-Virar", "Varanasi",
        "Srinagar", "Aurangabad", "Dhanbad", "Amritsar", "Navi Mumbai",
        "Allahabad", "Ranchi", "Howrah", "Coimbatore", "Jabalpur",
        "Gwalior", "Vijayawada", "Jodhpur", "Madurai", "Raipur",
        "Kota", "Chandigarh", "Guwahati", "Solapur", "Hubli-Dharwad",
        "Mysore", "Tiruchirappalli", "Bareilly", "Aligarh", "Tiruppur",
        "Moradabad", "Jalandhar", "Bhubaneswar", "Salem", "Warangal",
        "Mira-Bhayandar", "Thiruvananthapuram", "Bhiwandi", "Saharanpur", "Guntur",
        "Amravati", "Bikaner", "Noida", "Jamshedpur", "Bhilai",
        "Cuttack", "Firozabad", "Kochi", "Nellore", "Bhavnagar",
        "Dehradun", "Durgapur", "Asansol", "Rourkela", "Nanded",
        "Kolhapur", "Ajmer", "Akola", "Gulbarga", "Jamnagar",
        "Ujjain", "Loni", "Siliguri", "Jhansi", "Ulhasnagar",
        "Jammu", "Sangli-Miraj", "Mangalore", "Erode", "Belgaum",
        "Ambattur", "Tirunelveli", "Malegaon", "Gaya", "Udaipur"
    ]

    for i, query in enumerate(queries):
        city_name = places_in_india[i]
        city_name_lower = city_name.lower()

        # Create city folder with lowercase name
        city_folder = os.path.join(data_folder, city_name_lower)
        if not os.path.exists(city_folder):
            os.makedirs(city_folder)

        # Get search results
        exa_response = search_exa(query=query)

        # Write text file with lowercase name
        text_file_path = os.path.join(city_folder, f"{city_name_lower}.txt")
        with open(text_file_path, "w", encoding="utf-8") as f:
            f.write(exa_response["text"])

        # Write image link file
        img_file_path = os.path.join(city_folder, "img.txt")
        with open(img_file_path, "w", encoding="utf-8") as f:
            if exa_response["image"]:
                f.write(exa_response["image"])
            else:
                f.write("")

        print(f"Processed: {city_name}")



# if __name__ == "__main__":
#     main()