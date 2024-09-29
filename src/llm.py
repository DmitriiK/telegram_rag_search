from dotenv import load_dotenv
from typing import List
import logging
import json

from openai import OpenAI
import src.config as cfg
from src.data_classes import TelegaMessage, convert_to_json_list

load_dotenv()

client = OpenAI()
TOTAL_SPEND = 0 # spend USD for input output tokens


def ask_llm(prompt, model=cfg.llm_model):
    global TOTAL_SPEND
    if len(prompt) > 100000:
        raise Exception("Prompt is too big")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    logging.info(f'number of prompt_tokens: {response.usage.prompt_tokens}; completion tokens: {response.usage.completion_tokens}')
    amount_spend = (response.usage.prompt_tokens * cfg.llm_price[0] + response.usage.completion_tokens * cfg.llm_price[1])/1000000
    TOTAL_SPEND += amount_spend
    logging.info(f'amount_spend total:{TOTAL_SPEND:.5f}, last: {amount_spend:.5f} USD')
    return response.choices[0].message.content


def get_pure_json_from_llm_result(llr_ret:  str):
    llr_ret = llr_ret.replace('```json', '').replace('```', '')
    return json.dumps(json.loads(llr_ret), indent=4,  ensure_ascii=False)


def build_summarization_prompt(messages: List[TelegaMessage], chat_description: str = '') -> str:
    prompt_template = """
You will be given some json data, having  some sequence of messages from Telegram chat, mostly in Russian.
{chat_description}
Sequence is ordered by "msg_date"  (message date ).
There will be two types of messages, 
- the first one is "is_in_family" - and that means that they are explicitly linked in parent child relationship to each other by  "reply_to_msg_id"  attribute.  If there are no value for reply_to_msg_id for one of such messages, -that means this message is a root of such tree, probably starting discussion on some topic.
- the second one, where "is_in_family" == False, - do not have explicit relation to main tree of discussion.
They can be related to it or not, so were are consider them as "family candidates"

Please mind "reply_to_msg_id" values -it points to the message for which the current one is a reply. 
Thus, all messages linked by this reference, are more likely belong to one topic. 
And if some message that is initially "family candidate" is attributed to "family" - you need to add to topic (family) all the tree of descendant messages, if any.

Need to analyze the messages that are "in family", extract main subject of discussion (topic), 
and then  for each message not in family make a decision, - whether the message is related to main subject or not.

Ultimately you should output in json format following:
- topic name  (should be up to 7 words, in Russian)
- topic name eng  (same in English)
- topic summary (up to 50 words, for long topics may consist from up to 4 sentences in Russian)
- topic summary eng (same in English)
- topic tags: list of words for tagging, in Russian
- topic tags eng: same list but in English
- msg_ids: list of IDs for relevant for this topic messages, it supposed to contains ids for most of the messages in_family and some of the not in_family. 
- questions: list of 2 possible questions, in English,  for which the answer can be found 'topic' messages.
- answers: answers for each of the questions above. The source for that answers should be data from relevant messages, related to the topic

Final output should be pure parsible to dict json, without any additional comments.
--
example of usage:
for set of messages:
`

        "msg_id": 123,
        "msg_date": "2024-08-29T10:14:18",
        "user_name": "Dima",
        "reply_to_msg_id": null,
        "msg_text": "What kind of motor oil do you recommend to put in a Volkswagen car?",
        "is_in_family": True

        "msg_id": 124,
        "msg_date": "2024-08-29T10:14:18",
        "user_name": "John",
        "reply_to_msg_id": null,
        "msg_text": "I prefer Shell oil. But change it every 6 month",
        "is_in_family": False

        "msg_id": 126,
        "msg_date": "2024-08-29T10:14:18",
        "user_name": "Janet",
        "reply_to_msg_id": null,
        "msg_text": "I have a nice cat",
        "is_in_family": False

        "msg_id": 127,
        "msg_date": "2024-08-29T10:14:18",
        "user_name": "George",
        "reply_to_msg_id": 124,
        "msg_text": "Shell sucks. Buy Motul",
        "is_in_family": False

        "msg_id": 128,
        "msg_date": "2024-08-29T10:14:18",
        "user_name": "Paul",
        "reply_to_msg_id": 123,
        "msg_text": "VW sucks. Buy Toyota car, and you will not need to change oil at all",
        "is_in_family": True
`
topic_name might be: "recommendation for choosing of motor oil for VW".
"topic_summary_eng" might be:  
"as an motor oil for VS   recommended Shell and  Motul. But somebody recommends to have Toyota car instead of VW"".
relevant_messages_ids:  [124, 127, 128]
# 126 - not included cause it is of-topic.
    _________So, let's play._____
The messages, that you need to summirize into one topic are:
    `{messages}`
    """

    msg_json = convert_to_json_list(messages)
    return prompt_template.format(chat_description=chat_description, messages=msg_json)


def build_rag_prompt(question: str, chat_description:  str, messages: List[TelegaMessage]):
    prompt_template = """
    You will be given some data. That data is a sequence of messages from chat from some messager.
    It can be in English or Russian language.
    This sequnce will be given in json format.
    This chat is devoted to {chat_description}.

    The data that is provided for you will contain msg_id field for each message.
    Please mind "reply_to_msg_id" values -it points to the message for which the current one is a reply. 
    Thus, all messages linked by this reference, are more likely belong to one topic branch.

    You output should be some summarization text, answering the question,  maybe several sentences, if there is enough information to tell about,
    and the id-s for the messages, that are relevant to the question and which you use for the answer.
    Use English language for the output.
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
            Though user Paul suggested just to buy Toyota instead of VW."
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
    return prompt_template.format(question=question, chat_description=chat_description, messages=msg_json)


def build_translation_prompt(msgs_json: str) -> str:
    prompt_template = """
You will be given json dump of messages from Telegram chat in Russian.
Need to translate it to English.
Please mind "reply_to_msg_id" field,  it points to another message, been posted earlier,  
as specifies that the current message is a reply to another one.
Return pure json, without any explanations,  with same structure, but with msg_id and msg_text fields only.

The messages, that you need to translate are:
```json
    {messages}
```
    """
    return prompt_template.format( messages=msgs_json)


