import os
import uuid

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage,SystemMessage
from langchain_community.llms import OpenAI
from langchain_openai.chat_models import ChatOpenAI
from twilio.rest import Client
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request
from agent.tool import get_disaster_declaration,is_in_evacuation_zone,get_weather_alerts,get_power_outage_map, get_nearest_shelter,get_nearest_hospital,get_nearest_fire_station,query_rag_system
from agent.graph import create_graph

app = Flask(__name__)
account_sid = os.environ['ACCOUNT_SID']
auth_token = os.environ['AUTH_TOKEN']
client = Client(account_sid, auth_token)

# LLM and Tools Setup
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Replace these with the actual tool implementations
tools = [
    get_disaster_declaration,
    is_in_evacuation_zone,
    get_weather_alerts,
    get_power_outage_map,
    get_nearest_hospital,
    get_nearest_fire_station,
    get_nearest_shelter,
    query_rag_system
]

primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant specializing in providing disaster-related information and data from FEMA sources. "
            "Your focus is on helping users access, interpret, and utilize FEMA data effectively, especially related to disaster declarations, "
            "emergency response, and regional support for disaster zones. "
            "When searching, be persistent and thorough. Use multiple resources and approaches to find the most accurate, relevant information.",
        ),
        ("placeholder", "{messages}"),
    ]
)

graph = create_graph(tools=tools,
                        llm=llm,
                        system_prompt=primary_assistant_prompt)

def send_whatsapp(body:str,to_number:str):
    message = client.messages.create(
    from_=f"whatsapp:{os.environ['TWILIO_WHATSAPP']}",
    body=body,
    to=f'whatsapp:{to_number}'
    )

    print(message.sid)

@app.route('/whatsapp',methods=['POST'])
def receive_whatsapp():
    from_number = request.form['From']
    body = request.form['Body']
    print(f"Message from {from_number}: {body}")

    # Unique thread ID for each conversation
    thread_id = str(uuid.uuid4())

    # Maintain chat history
    chat_history = []

    # Add user input to chat history
    chat_history.append(HumanMessage(content=body))

    # Graph invocation
    config = {
        "configurable": {
            "thread_id": thread_id,  # Use thread ID for session management
        }
    }

    response = graph.invoke({"messages":chat_history},
                            config=config)
    graph_response = response["messages"][-1].content
    chat_history.append(SystemMessage(content=graph_response))

    ## send message
    send_whatsapp(graph_response,from_number)
    return "Message sent"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
