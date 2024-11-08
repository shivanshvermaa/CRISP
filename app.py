import chainlit as cl
import os
import yaml
import uuid
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage,SystemMessage
from langchain_community.llms import OpenAI
from langchain_openai.chat_models import ChatOpenAI
from langchain.chains import LLMChain

from agent.tool import get_disaster_declaration
from agent.graph import create_graph

import dotenv
dotenv.load_dotenv()

@cl.on_chat_start
def main():
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    tools = [get_disaster_declaration]

    primary_assistant_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant specializing in providing disaster-related information and data from FEMA sources. "
                "Your focus is on helping users access, interpret, and utilize FEMA data effectively, especially related to disaster declarations, "
                "emergency response, and regional support for disaster zones. "
                "When searching, be persistent and thorough. Use multiple resources and approaches to find the most accurate, relevant information."
            ),
            ("placeholder", "{messages}"),
        ]
    )



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
    chat_history.append(SystemMessage(content=graph_response))
    await cl.Message(graph_response).send()
