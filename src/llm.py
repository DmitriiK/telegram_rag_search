from dotenv import load_dotenv
from typing import List
import logging
from openai import OpenAI
import src.config as cfg
from src.data_classes import TelegaMessage, convert_to_json_list

load_dotenv()

client = OpenAI()


def ask_llm(prompt, model=cfg.llm_model):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    logging.info(f'number of prompt_tokens: {response.usage.prompt_tokens}; completion tokens: {response.usage.completion_tokens}')
    amount_spend = (response.usage.prompt_tokens * cfg.llm_price[0] + response.usage.completion_tokens * cfg.llm_price[1])/1000000
    logging.info(f'amount_spend {amount_spend:.5f} USD')
    return response.choices[0].message.content


def build_rag_prompt(question: str, chat_desciption:  str, messages: List[TelegaMessage]):
    prompt_template = """
    You will be given some data. That data is a sequence of messages from chat from some messager.
    This sequnce will be given in json format.
    This chat is devoted to {chat_desciption}.

    The data that is provided for you will contain msg_id field for each message.
    Please mind "reply_to_msg_id" values -it points to the message for which the current one is a reply. 
    Thus, all messages linked by this reference, are more likely belong to one topic branch.

    You output should be some summarization text, answering the question,  maybe several sentences, if there is enough information to tell about,
    and the id-s for the messages, that are relevant to the question and which you use for the answer.
    Final result should be just pure json with attributes described above, "answer", "msg_ids"
    If there are no relevant information inside the messages - just give empty values for both attributes
______
example of usage:
for set of messages:
`
        "msg_id": 123,
        "msg_date": "2024-08-29T10:14:18",
        "user_name": "Dima",
        "reply_to_msg_id": null,
        "msg_text": "What kind of motor oil do you recommend to put in a Volkswagen car?",

        "msg_id": 124,
        "msg_date": "2024-08-29T10:14:18",
        "user_name": "John",
        "reply_to_msg_id": null,
        "msg_text": "I prefer Shell oil. But change it every 6 month",

        "msg_id": 126,
        "msg_date": "2024-08-29T10:14:18",
        "user_name": "Janet",
        "reply_to_msg_id": null,
        "msg_text": "I have a nice cat"

        "msg_id": 127,
        "msg_date": "2024-08-29T10:14:18",
        "user_name": "George",
        "reply_to_msg_id": 124,
        "msg_text": "Shell sucks. Buy Motul",

        "msg_id": 128,
        "msg_date": "2024-08-29T10:14:18",
        "user_name": "Paul",
        "reply_to_msg_id": 123,
        "msg_text": "VW sucks. Buy Toyota car, and you will not need to change oil at all"

`

    and question: "A have Audi car. What motor oil is better for me?"
    the result might be:
    `
    {{
        answer: "As Audi is part of VW brand, it might be either Shell or Motul.
            But for Shell keep in mind to change it every 6 months.
            Though user Paul suggested just to buy Toyota instead of VS."
        msg_ids: [123,124, 127, 128]
    }}
    `
    # note: 126 is no included as it is not relevant for this question
    _________So, let's play._____
     The question, for which you should give the answer is:
    '{question}'.
    And the messages, where you can potentially find necessary information are:
    `{messages}`
    """
    msg_json = convert_to_json_list(messages)
    return prompt_template.format(question=question, chat_desciption=chat_desciption, messages=msg_json)



