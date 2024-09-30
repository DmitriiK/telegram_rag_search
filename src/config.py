from datetime import timedelta  
import yaml

# distance in timedelta for topic candidate messages, - we are conidering 2 hours before and 2 hours after messages
near_messages_time_delta = timedelta(hours=2)

# OR we are considering 3 messages before and 3 messages after
near_messages_number_of_messages_delta = 3

telegram_group_id = 1688539638  # Kebab Antalia
chat_description = 'Life or russian relocants in Antalya'

es_url = 'http://localhost:9200'
elastic_search_index_config_path = "src/elastic_search/index_settings.yml"

messages_dump_path = "/Users/dklmn/Documents/data/telega/result.json"
topics_path = 'output/llm_output/topics.json' 

index_name_topics = 'telegram-topics'
index_name_messages = "telegram-messages"
index_name_messages_eng = "telegram-messages-eng"
index_pk_fields = {index_name_topics: ['chat_id', 'topic_name'],
                   index_name_messages: ['chat_id', 'msg_id'],
                   index_name_messages_eng: ['chat_id', 'msg_id'],                  
                   }  # logical PKs for doc fields


sent_tranformer_model_name = 'distiluse-base-multilingual-cased-v1'

llm_model, llm_price = "gpt-4o-2024-08-06", (2.5, 10)  # input,output tokens, usd for 1M

# llm_model, llm_price = "gpt-4o-mini", (0.15, 0.6)  # input, output tokens, usd for 1M


def read_index_settings(index_name):
    with open(elastic_search_index_config_path, 'r') as file:
        data = yaml.safe_load(file)
        return data[index_name]
    
