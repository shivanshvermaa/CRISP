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

if __name__ == "__main__":
    # Configuration for the local folder and database
    local_folder_path = "/path/to/your/documents"
    index_table_name = "example_index"
    
    # Database configuration dictionary
    db_config = {
        "username": "your_db_username",
        "password": "your_db_password",
        "hostname": "localhost",
        "port": 5432,
        "dbname": "your_db_name"
    }

    # Chunk size and overlap settings
    chunk_size = 256  # Number of tokens or characters per chunk
    chunk_overlap = 32  # Overlapping tokens/characters between chunks

    # Embedding model to use (e.g., OpenAI's text-embedding-ada-002)
    embedding_model = "text-embedding-ada-002"

    # Check if the local folder path exists
    if not os.path.exists(local_folder_path):
        raise FileNotFoundError(f"Local folder path does not exist: {local_folder_path}")

    # Run the indexer with the specified parameters
    try:
        run_indexer(
            local_folder_path=local_folder_path,
            db_config=db_config,
            index_table_name=index_table_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            embedding_model=embedding_model
        )
        print("Ingestion and indexing process completed successfully.")
    except Exception as e:
        print(f"An error occurred during the ingestion process: {e}")
```

### Retrieval Code

```python
import requests

# Define the URL of your Flask server
url = "http://localhost:5015/ask"
headers = {"Content-Type": "application/json"}

# Prepare the request data
query_data = {
    "q": "Which location are they talking about?",
    "index": "temp",
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
