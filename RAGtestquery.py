import requests

# Define the URL of your Flask server
url = "http://localhost:5015/ask"
headers = {"Content-Type": "application/json"}

# Prepare the request data
query_data = {
    "q": "what should be my plan to evacuate in case of a Hurricane",
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
