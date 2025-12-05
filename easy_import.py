import os
import sys
import subprocess
import time

def run_command(command):
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 easy_import.py <path_to_txt_file> [image_url]")
        return

    file_path = sys.argv[1]
    image_url = sys.argv[2] if len(sys.argv) > 2 else ""

    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found locally.")
        return

    filename = os.path.basename(file_path)
    container_name = "smarttour-search-1"

    print(f"--- Step 1: Syncing Scripts & Data to Docker ---")
    # Copy the data file
    if not run_command(f"docker cp {file_path} {container_name}:/app/{filename}"):
        return
    # Copy the scripts (to ensure latest logic is used)
    if not run_command(f"docker cp import_destination.py {container_name}:/app/import_destination.py"):
        return
    if not run_command(f"docker cp sync_mongo_to_chroma.py {container_name}:/app/sync_mongo_to_chroma.py"):
        return

    print(f"--- Step 2: Importing Data to MongoDB ---")
    if not run_command(f"docker exec {container_name} python import_destination.py {filename} \"{image_url}\""):
        return

    print(f"--- Step 3: Updating AI Embeddings (ChromaDB) ---")
    if not run_command(f"docker exec {container_name} python sync_mongo_to_chroma.py"):
        return

    print("\n✅ Success! Destination added and AI updated.")

if __name__ == "__main__":
    main()
