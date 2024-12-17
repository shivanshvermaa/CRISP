import chainlit as cl
import subprocess
import os
import yaml
import uuid
import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage,AIMessage
from langchain_community.llms import OpenAI
from langchain_openai.chat_models import ChatOpenAI
from langchain.chains import LLMChain

from agent.tool import get_disaster_declaration,is_in_evacuation_zone,get_weather_alerts,get_power_outage_map,get_nearest_hospital,get_nearest_fire_station, get_nearest_shelter,query_rag_system
from agent.graph import create_graph

import dotenv
dotenv.load_dotenv()

# Start the Flask server as a subprocess
#def start_flask_server():
#    subprocess.Popen(["python", "rag/retriever.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#start_flask_server()
@cl.on_chat_start
def main():
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    tools = [get_disaster_declaration,
             is_in_evacuation_zone,
             get_weather_alerts,
             get_power_outage_map,
             get_nearest_hospital,
             get_nearest_fire_station,
             get_nearest_shelter,
             query_rag_system]

    # TODO Improve this zx
    primary_assistant_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert assistant specializing in disaster-related information and resources. Your role is to help users effectively access, interpret, and utilize data related to disaster declarations, emergency response, preparedness, and regional support. You draw on multiple trusted sources, including FEMA, government agencies, NGOs, and verified public data. Your responses must be precise, actionable, and up-to-date, using the current datetime for accuracy: {datetime}. Be thorough, persistent, and resourceful, ensuring the information you provide is relevant, reliable, and comprehensive."
            ),
            ("placeholder", "{messages}"),
        ]
    ).partial(datetime=datetime.datetime.now())



    graph = create_graph(tools=tools,
                         llm=llm,
                         system_prompt=primary_assistant_prompt)

    chat_history = []
    thread_id = str(uuid.uuid4())

    cl.user_session.set("graph", graph)
    cl.user_session.set("chat_history", chat_history)
    cl.user_session.set("thread_id",thread_id)

@cl.on_message
async def main(message):
    graph = cl.user_session.get("graph")
    chat_history = cl.user_session.get("chat_history")
    thread_id = cl.user_session.get("thread_id")

    question = message.content

    config = {
        "configurable": {
            # This thread ID is used to like handle conversation history and stuff
            "thread_id": thread_id,
        }
    }

    chat_history.append(HumanMessage(content=question))
    response = graph.invoke({"messages":chat_history},
                            config=config)
    graph_response = response["messages"][-1].content
    chat_history.append(AIMessage(content=graph_response))
    await cl.Message(graph_response).send()
