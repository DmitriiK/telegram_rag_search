## RAG based search over Telegram Messages
Features:
- retrieving of Telegram messages from exported data or directrly though Telegram API
- Building of "Topic tree" from these messages, using LLM
- Summarization of data in such topics, using LLM
- Indexing of that data in Elastic Search
- Search over that data using both simple search and semantic (vector embedding) search
- RAG, - Answering of users questions, using combination of Elastic Search to retrieve potentially relevant data, feeding that to LLM that should ultimately evaluate the relevance of data and provide the answer