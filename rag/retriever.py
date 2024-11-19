from dotenv import load_dotenv
from flask import Flask, request, jsonify
import os
import sys
import logging
import tiktoken
from sqlalchemy import make_url
from llama_index.core import VectorStoreIndex, get_response_synthesizer, Settings, set_global_handler, PromptTemplate
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.response_synthesizers import BaseSynthesizer
from llama_index.core.retrievers import BaseRetriever, VectorIndexRetriever
from llama_index.core.schema import MetadataMode
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.postgres import PGVectorStore
import psycopg2
from indexer import run_indexer 



load_dotenv()

sys.stdout.reconfigure(encoding='utf-8')

embed_model = OpenAIEmbedding(model="text-embedding-3-small")
llm = OpenAI(model="gpt-4o-mini")

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

Settings.llm = llm
Settings.embed_model = embed_model
Settings.num_output = 2048

token_counter = TokenCountingHandler(
    tokenizer=tiktoken.encoding_for_model("gpt-3.5-turbo").encode
)

class RAGQueryEngine(CustomQueryEngine):
    retriever: BaseRetriever
    response_synthesizer: BaseSynthesizer

    def custom_query(self, query_str: str, conversation_history: str = ""):
        nodes = self.retriever.retrieve(query_str)
        if not nodes:
            logging.warning("No relevant nodes found for the query.")
            # Create a simple response object with a 'response' attribute.
            response_obj = type("Response", (object,), {"response": "No relevant information found"})
            return response_obj, []


        i = 0
        rag_retrieved_details = []
        logging.info("Retrieved nodes:")
        for x in nodes:
            i += 1
            logging.info(f"Node {i}: {x.get_text()[:100]} (Score: {x.get_score()})")
            docu_info = {
                'chunk': x.get_text(),
                'score': x.get_score(),
                'node_id': x.node_id,
                'file_name': x.metadata.get('file_name', 'Unknown')
            }
            rag_retrieved_details.append(docu_info)

        response_obj = self.response_synthesizer.synthesize(query_str, nodes, conversation_history=conversation_history)
        if not response_obj.response:
            response_obj.response = "No relevant information found."

        return response_obj, rag_retrieved_details


query_engines = {}
DEFAULT_QA_TEMPLATE = (
    "Context information is below.\n"
    "---------------------\n{context_str}\n---------------------\n"
    "Conversation history is below.\n"
    "---------------------\n{conversation_history}\n---------------------\n"
    "Given the context information, conversation history, and not prior knowledge, answer the query.\n"
    "Query: {query_str}\nAnswer: "
)

def get_query_engine_by_index_name(name, prompt='', conversation_history='', top_k=5):
    print(f"Initializing query engine for index: '{name}'")
    table_name = "rag_" + name
    print(f"Using table name: {table_name}")

    if name not in query_engines:
        url = make_url(os.getenv("VECTOR_DATABASE_URL"))
        try:
            print("Connecting to vector store with URL parameters:")
            print(f"Database: {url.database}, Host: {url.host}, User: {url.username}, Port: {url.port}")
            
            vector_store = PGVectorStore.from_params(
                database=url.database,
                host=url.host,
                password=url.password,
                port=url.port,
                user=url.username,
                table_name=table_name,
                embed_dim=1536,
            )
            print("Vector store initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing vector store for index '{name}': {e}")
            return None

        if prompt == '':
            prompt = DEFAULT_QA_TEMPLATE
        else:
            prompt = DEFAULT_QA_TEMPLATE + prompt

        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        print("VectorStoreIndex created successfully.")

        text_qa_template = PromptTemplate(prompt)
        query_engine = RAGQueryEngine(
            retriever=VectorIndexRetriever(
                index=index,
                similarity_top_k=top_k,
            ),
            response_synthesizer=get_response_synthesizer(
                text_qa_template=text_qa_template,
                response_mode="compact"
            ),
        )
        query_engines[name] = query_engine
        print(f"Query engine for '{name}' added to cache.")
    else:
        print(f"Using cached query engine for index: '{name}'")
        if prompt != '':
            query_engines[name].response_synthesizer = get_response_synthesizer(
                text_qa_template=PromptTemplate(prompt),
                response_mode="compact"
            )
        query_engines[name].retriever.similarity_top_k = top_k

    return query_engines[name]

class RAGQueryEngine(CustomQueryEngine):
    retriever: BaseRetriever
    response_synthesizer: BaseSynthesizer

    def custom_query(self, query_str: str, conversation_history: str = ""):
        print(f"Executing custom query: '{query_str}' with conversation history: '{conversation_history}'")
        nodes = self.retriever.retrieve(query_str)
        if not nodes:
            logging.warning("No relevant nodes found for the query.")
            # Create a more complete response object with the required methods
            class Response:
                def __init__(self):
                    self.response = "No relevant information found"

                def get_formatted_sources(self):
                    return []

            response_obj = Response()
            return response_obj, []

        i = 0
        rag_retrieved_details = []
        logging.info("Retrieved nodes:")
        for x in nodes:
            i += 1
            logging.info(f"Node {i}: {x.get_text()[:100]} (Score: {x.get_score()})")
            print(f"Metadata for Node {i}: {x.metadata}")
            docu_info = {
                'chunk': x.get_text(),
                'score': x.get_score(),
                'node_id': x.node_id,
                'file_name': x.metadata.get('file_name', 'Unknown')
            }
            rag_retrieved_details.append(docu_info)

        response_obj = self.response_synthesizer.synthesize(query_str, nodes, conversation_history=conversation_history)
        if not response_obj.response:
            response_obj.response = "No relevant information found."

        return response_obj, rag_retrieved_details

app = Flask(__name__)

@app.route('/ask', methods=['GET', 'POST'])
def query_kb():
    print("Received request...")
    question = ''
    index = ''
    prompt = ''
    top_k_str = '5'
    conversation_history = ''

    if request.method == 'GET':
        question = request.args.get('q', '')
        index = request.args.get('index', '')
    elif request.method == 'POST':
        data = request.get_json()
        question = data.get('q', '')
        index = data.get('index', '')
        prompt = data.get('prompt', '')
        top_k_str = data.get('top_k', '5')
        conversation_history = data.get('conversation_history', '')

    if index == '':
        index = "test"

    if conversation_history == '':
        conversation_history = "No conversation history provided"

    top_k = int(top_k_str)

    print(f"Question: {question}")
    print(f"Index: {index}, Top K: {top_k}, Conversation History: {conversation_history}")

    token_counter.reset_counts()

    query_engine = get_query_engine_by_index_name(index, prompt, conversation_history, top_k)
    if query_engine is None:
        print("Failed to initialize query engine.")
        return jsonify({"error": "Failed to initialize query engine for the given index."}), 500

    response, rag_chunk_details = query_engine.custom_query(question, conversation_history)
    if not hasattr(response, 'response'):
        print("Response object does not have 'response' attribute.")
        return jsonify({"response": "No relevant information found.", "rag_chunk_details": []})

    print("Response:", response.response)

    response_data = {
        'response': response.response,
        'sources': response.get_formatted_sources(),
        'total_embedding_token_count': token_counter.total_embedding_token_count,
        'prompt_llm_token_count': token_counter.prompt_llm_token_count,
        'completion_llm_token_count': token_counter.completion_llm_token_count,
        'total_llm_token_count': token_counter.total_llm_token_count,
        'rag_chunk_details': rag_chunk_details
    }

    return jsonify(response_data)



@app.route('/run_indexer', methods=['POST'])
def run_indexer_endpoint():
    try:
        data = request.get_json()
        folder_path = data['folder_path']
        index_table_name = data['index_table_name']
        chunk_size = data.get('chunk_size', 512)
        chunk_overlap = data.get('chunk_overlap', 64)

        run_indexer(folder_path, index_table_name, chunk_size, chunk_overlap)
        return jsonify({"status": "Indexing complete"}), 200
    except Exception as e:
        logging.error(f"Error running indexer: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=5015)