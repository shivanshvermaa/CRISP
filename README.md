# Title Here


## Prerequisites

- PostgreSQL 13+ installed
- `pgvector` extension installed
- Python 3.x installed

## Installation steps for Vector-Based Retrieval System with PostgreSQL and pgvector

### 1. Install PostgreSQL

Make sure PostgreSQL version 13 or higher is installed on your system.

### 2. Install `pgvector`

Follow the installation steps from the [pgvector GitHub repository](https://github.com/pgvector/pgvector). On Linux, ensure PostgreSQL is installed before proceeding.

### 3. Create PostgreSQL Database and Enable Vector Extension

Connect to your PostgreSQL server using the `psql` command:

```bash
psql --host localhost --username postgres --dbname vectordb
```

Run the following commands in the PostgreSQL shell:

```sql
CREATE ROLE postgres WITH SUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD '<password>';
CREATE EXTENSION IF NOT EXISTS vector;
```

### 4. Start PostgreSQL Server

Use the following command to start the PostgreSQL server:

```bash
pg_ctl start
```

### 5. Create a Database

Create a new database for your project:

```bash
createdb <database_name>
```

### 6. Start the Python Server

Run the retrieval server with the following command:

```bash
python retriever.py runserver
```

> **Note:** This command currently starts `retriever.py`. There is a TODO to combine it with `app.py`.

## Ingestion and Retrieval

Below is a sample code snippet for ingestion and retrieval queries.

### Ingestion Code

```python
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
    local_folder_path = "path"
    index_table_name = "test"
    
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
```

### Retrieval Code

```python
import requests

# Define the URL of your Flask server
url = "http://localhost:5015/ask"
headers = {"Content-Type": "application/json"}

# Prepare the request data
query_data = {
    "q": "what should be my plan to evacuate?",
    "index": "hurricanefirstaid",
    "prompt": "",
    "top_k": 5,
    "conversation_history": ""
}

# Disable proxy for local requests
proxies = {
    "http": None,
    "https": None
}

# Send the POST request
response = requests.post(url, json=query_data, headers=headers, proxies=proxies)

# Print the response from the server
if response.status_code == 200:
    result = response.json()
    print("Response:", result['response'])
    print("Sources:", result['sources'])
    print("Total Embedding Token Count:", result['total_embedding_token_count'])
    print("Prompt LLM Token Count:", result['prompt_llm_token_count'])
    print("Completion LLM Token Count:", result['completion_llm_token_count'])
    print("RAG Chunk Details:", result['rag_chunk_details'])
else:
    print("Error:", response.status_code, response.text)
```

## TODO

- [ ] Combine `retriever.py` with `app.py` for unified server execution.


## Notes

- Ensure the PostgreSQL server is running before starting the Python server.
- Configure the database settings in the ingestion code as per your environment.

## References

- [pgvector GitHub Repository](https://github.com/pgvector/pgvector)

---

Feel free to update this README as your project evolves!
