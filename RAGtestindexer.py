import os
import requests

if __name__ == "__main__":
    # Define the URL of your Flask server
    url = "http://localhost:5015/run_indexer"
    headers = {"Content-Type": "application/json"}
    # Disable proxy for local requests
    proxies = {
        "http": None,
        "https": None
    }

    # Configuration for the local folder and database
    local_folder_path = os.getcwd() + "/data/HurricaneFirstAid/"
    index_table_name = "hurricanefirstaid"
    
    # Chunk size and overlap settings
    chunk_size = 256  # Number of tokens or characters per chunk
    chunk_overlap = 32  # Overlapping tokens/characters between chunks

    # Check if the local folder path exists
    if not os.path.exists(local_folder_path):
        raise FileNotFoundError(f"Local folder path does not exist: {local_folder_path}")

    # Prepare the data to send in the POST request
    payload = {
        "folder_path": local_folder_path,
        "index_table_name": index_table_name,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap
    }

    # Send the POST request
    try:
        response = requests.post(url, json=payload, headers=headers, proxies=proxies)
        if response.status_code == 200:
            print("Ingestion and indexing process completed successfully.")
            print("Response:", response.json())
        else:
            print(f"Failed to run the indexer. Status Code: {response.status_code}")
            print("Error Response:", response.json())
    except Exception as e:
        print(f"An error occurred while making the request: {e}")