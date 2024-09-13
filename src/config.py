from datetime import timedelta  
import yaml

# distance in timedelta for topic candidate messages, - we are conidering 2 hours before and 2 hours after messages
near_messages_time_delta = timedelta(hours=2)

# OR we are considering 3 messages before and 3 messages after
near_messages_number_of_messages_delta = 3

telegram_group_id = 1688539638  # Kebab Antalia
chat_desciption = 'Life or russian relocants in Antalya'

es_url = 'http://localhost:9200'
elastic_search_index_config_path = "src/elastic_search/index_settings.yml"

messages_dump_path = "/Users/dklmn/Documents/data/telega/result.json"
topics_path = 'output/llm_output/topics.json' 

index_name_topics = 'telegram-topics'
index_name_messages = "telegram-messages"  
 
sent_tranformer_model_name = 'distiluse-base-multilingual-cased-v1'

llm_model = "gpt-4o-mini"

def read_index_settings(index_name):
    with open(elastic_search_index_config_path, 'r') as file:
        data = yaml.safe_load(file)
        return data[index_name]
    
