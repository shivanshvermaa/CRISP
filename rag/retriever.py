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
        i = 0
        rag_retrieved_details = []
        for x in nodes:
           i = i + 1
           print(f'## Document {i} ##')
           print(x)
           docu_info = {}
           docu_info['chunk'] = x.get_text()
           docu_info['score'] = x.get_score()
           docu_info['node_id'] = x.node_id
           docu_info['file_name'] = x.metadata['file_name']
           docu_info['container'] = x.metadata['container']
           rag_retrieved_details.append(docu_info)
           
        print('## END ##')

        response_obj = self.response_synthesizer.synthesize(query_str, nodes, conversation_history=conversation_history)
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
    if name not in query_engines:
        url = make_url(os.getenv("VECTOR_DATABASE_URL"))
        vector_store = PGVectorStore.from_params(
            database=url.database,
            host=url.host,
            password=url.password,
            port=url.port,
            user=url.username,
            table_name="rag_" + name,
            embed_dim=1536,
        )

        if (prompt == ''):
            prompt = DEFAULT_QA_TEMPLATE
        else:
            prompt = DEFAULT_QA_TEMPLATE + prompt

        index = VectorStoreIndex.from_vector_store(vector_store = vector_store)

        text_qa_template = PromptTemplate(prompt)
        query_engine  = RAGQueryEngine(
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=top_k,
            ),
            response_synthesizer = get_response_synthesizer(
                text_qa_template = text_qa_template,
                response_mode="compact"
            ),
        )
        query_engines[name] = query_engine
    else:
        if (prompt != ''):
            query_engines[name].response_synthesizer = get_response_synthesizer(
                text_qa_template = PromptTemplate(prompt),
                response_mode="compact"
            )
        query_engines[name].retriever.similarity_top_k = top_k
    return query_engines[name]


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

    #if (index == ''):
    #    index = "general"

    if (conversation_history == ''):
        conversation_history = "No conversation history provided"

    top_k = int(top_k_str)

    print("Question: " + question)

    token_counter.reset_counts()

    query_engine = get_query_engine_by_index_name(index, prompt, conversation_history, top_k)
    response, rag_chunk_details = query_engine.custom_query(question, conversation_history)

    print("Response: " + response.response)


   
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

@app.route('/status', methods=['GET'])
def kb_status():
    index = request.args.get('index', '')

    #if (index == '') or (not index.isidentifier()):
    #    index = "general"

    chunk_count = 0
    doc_count = 0
    recent_docs = []

    url = make_url(os.getenv("VECTOR_DATABASE_URL"))
    with psycopg2.connect(
            database = url.database,
            user = url.username,
            password = url.password,
            host = url.host,
            port = url.port) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM data_rag_{index}")
            chunk_count = cursor.fetchone()[0]

        with connection.cursor() as cursor:
            cursor.execute(f"select count(*) from (select distinct metadata_->>'file_name' from data_rag_{index}) as temp")
            doc_count = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT metadata_->>'file_name', metadata_->>'last_modified_date'
                FROM data_rag_{index}
                ORDER BY id DESC LIMIT 5
            """)
            recent_docs = [{'file_name': row[0], 'last_modified_date': row[1]} for row in cursor.fetchall()]

    response_data = {
        'index': index,
        'doc_count': doc_count,
        'chunk_count': chunk_count,
        'recent_docs': recent_docs
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
        embedding_model = data.get('embedding_model', 'text-embedding-ada-002')

        db_config = {
            'username': os.getenv('DB_USERNAME'),
            'password': os.getenv('DB_PASSWORD'),
            'hostname': os.getenv('DB_HOSTNAME'),
            'port': os.getenv('DB_PORT', 5432),
            'dbname': os.getenv('DB_NAME')
        }

        run_indexer(folder_path, db_config, index_table_name, chunk_size, chunk_overlap, embedding_model)
        return jsonify({"status": "Indexing complete"}), 200
    except Exception as e:
        logging.error(f"Error running indexer: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=5015)