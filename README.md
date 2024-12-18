
# CRISP - Crisis Response and Intelligent Support Platform
## Agent Hosted [on GCP]
<a href="http://35.184.51.67/" about="blank">Website</a> <br>
<a href="http://35.184.51.67:8000/" about="blank">CRISP[chat window]</a> <br>
<a href="https://youtu.be/6icHD-EJcmc" about="blank">Demo Video[Youtube]</a> <br>
#### Probable Issues with hosted site 
	• 	The website is hosted on a free GCP account if there are any concerns accessing the agent 
 		please contact the team at rampuriamanya51@gmail.com
 	•	The website is "HTTP://" so please continue even if it says unsafe
	•	Use the QR or contact given below to test WhatsApp texting
 <a href="https://drive.google.com/file/d/1MqPRhm1oswaZJhg1PgmvZ8owNMMvkDWH/view?usp=sharing" about="blank">Scan QR for whatsapp</a>
 	
## Problem Statement
	•	Hurricanes bring chaos: severe weather, evacuation needs, and infrastructure disruptions.
	•	Lack of centralized, real-time information makes decision-making difficult.
	•	Limited network connectivity during disasters restricts access to digital resources.
	•	Emergency services struggle with overwhelming demand and coordination challenges.
	•	Florida and Texas face these challenges repeatedly, requiring smarter disaster management solutions.
	•	Historical storms like Katrina and Harvey have shown the need for better real-time disaster response tools.

## Solution
	•	An AI-driven agent, CRISP provides real-time hurricane support for Florida and Texas.
	•	Accessible via WhatsApp Message, ensuring usability during low connectivity.
	•	A suite of tools for timely and actionable disaster-related insights:
	•	Evacuation zone alerts
	    -    Shelter, hospital, and fire station locations
    	-	First-aid and disaster preparation guidance (RAG)
    	-	Live weather and power outage updates

| Tool                     | Description                                                             |
|--------------------------|-------------------------------------------------------------------------|
| Get Disaster Declaration | Access official disaster declarations from FEMA.                       |
| Is in Evacuation Zone    | Checks if the user’s location is in an evacuation zone.                |
| Get Weather Alerts       | Real-time weather updates and warnings.                               |
| Get Power Outage Map     | Provides the latest power outage maps for affected regions.           |
| Get Nearest Shelter      | Lists shelters with status, capacity, and directions.                 |
| Get Nearest Hospital     | Locates the closest operational hospitals.                            |
| Get Nearest Fire Station | Shows the nearest emergency fire response units.                      |
| RAG Assistance           | Delivers first-aid tips and hurricane preparation guides.             |


## Table of Contents for PostgreSQL installation and RAG indexing.

- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup)
  - [1. Install Homebrew (macOS)](#1-install-homebrew-macos)
  - [2. Install PostgreSQL 14 via Homebrew](#2-install-postgresql-14-via-homebrew)
  - [3. Initialize the Homebrew Environment](#3-initialize-the-homebrew-environment)
  - [4. Start PostgreSQL via Homebrew Services](#4-start-postgresql-via-homebrew-services)
  - [5. Stop Existing Postgres Services (If Needed)](#5-stop-existing-postgres-services-if-needed)
  - [6. (Re)Initialize the PostgreSQL Data Directory](#6-reinitialize-the-postgresql-data-directory)
  - [7. Start PostgreSQL Server Manually (If Not Using Homebrew Services)](#7-start-postgresql-server-manually-if-not-using-homebrew-services)
  - [8. Verify the PostgreSQL Server is Running](#8-verify-the-postgresql-server-is-running)
  - [9. Create PostgreSQL Role and Database](#9-create-postgresql-role-and-database)
  - [10. Install pgvector Extension](#10-install-pgvector-extension)
- [Vector-Based Retrieval System Installation](#vector-based-retrieval-system-installation)
  - [1. Start the Python Server](#1-start-the-python-server)
  - [2. Ingestion and Retrieval](#2-ingestion-and-retrieval)
    - [Ingestion Code](#ingestion-code)
    - [Retrieval Code](#retrieval-code)
- [Troubleshooting](#troubleshooting)
  - [1. Permission Errors During initdb](#1-permission-errors-during-initdb)
  - [2. Cannot Run initdb as root](#2-cannot-run-initdb-as-root)
  - [3. Directory Already Exists](#3-directory-already-exists)
  - [4. Postgres Service Conflicts](#4-postgres-service-conflicts)
  - [5. Check Server Status and Logs](#5-check-server-status-and-logs)
- [TODO](#todo)
- [Notes](#notes)
- [References](#references)

---

## Prerequisites

- **Homebrew** (for macOS users)
- **PostgreSQL 14** installed
- **pgvector** extension installed
- **Python 3.x** installed

---

## Installation and Setup for Postgres

### 1. Install Homebrew (macOS)

If you are on macOS and do not have Homebrew installed, install it using the following command:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install PostgreSQL 14 via Homebrew

Install PostgreSQL version 14 using Homebrew:
```bash

brew install postgresql@14
```

### 3. Initialize the Homebrew Environment

Add Homebrew to your shell environment by executing the following commands:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### 4. Start PostgreSQL via Homebrew Services

Start PostgreSQL using Homebrew services:

```bash
brew services start postgresql@14
```

Verify that PostgreSQL is running:

```bash
brew services list
```

Ensure that postgresql@14 shows as “started” or similar.

### 5. Stop Existing Postgres Services (If Needed)

If you need to stop and manage Postgres manually, use:

```bash
brew services stop postgresql@14
```

### 6. (Re)Initialize the PostgreSQL Data Directory

If you need to start fresh and the data directory already exists, remove it first:

```bash
sudo rm -rf /usr/local/var/postgres

```
Then recreate the directory and set correct permissions:

```bash
sudo mkdir -p /usr/local/var/postgres
sudo chown -R $(whoami) /usr/local/var/postgres
chmod 700 /usr/local/var/postgres

```
Initialize the database:

```bash
initdb -D /usr/local/var/postgres

```
This should complete without permission errors.

### 7. Start PostgreSQL Server Manually (If Not Using Homebrew Services)

Start PostgreSQL manually:

```bash
pg_ctl -D /usr/local/var/postgres start

```
Alternatively, if you prefer using Homebrew services:

```bash
brew services start postgresql@14

```
### 8. Verify the PostgreSQL Server is Running

Check the status of the PostgreSQL server:

```bash
pg_ctl -D /usr/local/var/postgres status

```
Or simply try connecting:

```bash
psql postgres

```
If you connect successfully, the server is running.

### 9. Create PostgreSQL Role and Database

Once connected to psql (using psql postgres), create a PostgreSQL role with password and superuser privileges:

```bash
CREATE ROLE postgres WITH SUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD '<password>';

```
Replace <password> with your desired password.

Then, create the vectordb database:

```bash
CREATE DATABASE vectordb;

```
### 10. Install pgvector Extension

Clone, build, and install the pgvector extension:

```bash
cd /tmp
git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

```
After installing, connect to your vectordb database:

```bash
psql --host localhost --username postgres --dbname vectordb

```
Enable the vector extension:

```bash
CREATE EXTENSION IF NOT EXISTS vector;

```
This should successfully load pgvector into vectordb.

Vector-Based Retrieval System Installation

#### 1. Start the Python Server

Run the retrieval server with the following command:

```bash
python retriever.py runserver

```
	Note: This command currently starts retriever.py. There is a TODO to combine it with app.py.

#### 2. Ingestion and Retrieval

Below are sample code snippets for ingestion and retrieval queries. 
#### NOTE: nake sure documents are present in folder  -- os.getcwd() + "/data/<foldername>/" . Modify the table name as required.  In the below code , folder is os.getcwd() + "/data/HurricaneFirstAid/" and the table name selected is hurricanefirstaid. 
 
Example of Ingestion Code

```bash
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
    local_folder_path = os.getcwd() + "/data/HurricaneFirstAid/"  # Path of folder with files to index
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

```
Example of Retrieval Code

```bash
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
### Troubleshooting

### 1. Permission Errors During initdb

If you encounter an error like could not change permissions of directory ...: Operation not permitted, ensure the directory /usr/local/var/postgres is owned by your user and has correct permissions:

```bash
sudo chown -R $(whoami) /usr/local/var/postgres
chmod 700 /usr/local/var/postgres

```
Then run:

```bash
initdb -D /usr/local/var/postgres

```
### 2. Cannot Run initdb as root

If you run initdb with sudo or as root, it will fail. Run initdb as the non-root user who will own the server process.

### 3. Directory Already Exists

If initdb complains the directory is not empty, remove it if you want a fresh start:

```bash
sudo rm -rf /usr/local/var/postgres

```
Then recreate, adjust permissions, and re-run initdb.

### 4. Postgres Service Conflicts

If you have multiple versions of PostgreSQL running (e.g., different ports), ensure only one instance is running on port 5432, or adjust postgresql.conf to use a different port. Use the following command to identify processes occupying port 5432:

```bash
lsof -i :5432

```
Then stop or kill the conflicting processes as needed.

### 5. Check Server Status and Logs

If pg_ctl indicates a failure, check the log file you passed with -l logfile or inspect /usr/local/var/postgres/server.log if it exists. This may provide clues on what’s wrong.

Notes

	•	Ensure the PostgreSQL server is running before starting the Python server.
	•	Configure the database settings in the ingestion code as per your environment.

References

	•	

Feel free to update this README as your project evolves!

---
