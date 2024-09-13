from dotenv import load_dotenv
from typing import List
import logging
from openai import OpenAI
import src.config as cfg
from src.data_classes import TelegaMessage, convert_to_json_list

load_dotenv()

client = OpenAI()


def llm(prompt, model=cfg.llm_model):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

def build_rag_prompt(question: str, chat_desciption:str, messages: List[TelegaMessage]):
    prompt_template = """
    You will be given some data. That data is a sequence of messages from chat from some messager.
    This sequnce will be given in json format.
    This chat is devoted to {chat_desciption}.
    The question, for which you should give the answer is:
    '{question}'.

    The data that is provided for you will contain msg_id field for each message. 
    You should output the id-s for the messages, that are relevant to the question and which you use for the answer.
    The date - where you can try to find additional information to answer the question is:
    ---
    {messages}
    Example, for messages like this 
    ---
        "msg_id": 123;   "msg_text": "What kind of motor oil do you recommend to put in a Volkswagen car?"   
        "msg_id": 124;   "msg_text": "I prefer Shell oil. But change it every 6 month"
        "msg_id": 127;    "msg_text": "Shell sucks. Buy Motul"
        "msg_id": 128;    "msg_text": "VW sucks. Buy Toyota car, and you will not need to change oil at all"
    --
    and question: "A have Audi car. What motor oil is better for me?"
    the result might be:
    {{
        answer: "As Audi is part of VW brand, it might be either Shell or Motul."
        msg_ids: [123,124, 127]
    }}
    # note: 128 is no included as it is not relevant for this question
    --
    If there are no relevant information inside the messages - just give empty values.
    """
    msg_json = convert_to_json_list(messages)
    return prompt_template.format(question=question, chat_desciption=chat_desciption, messages=msg_json)



