# LLM-Based RAG Search Over Telegram Messages

## Overview
![image](https://github.com/user-attachments/assets/89ebf96e-bc44-4a99-a7ee-c0126ef0d62b)


This repository implements functionalities for retrieving and processing Telegram messages, specifically focusing on using Large Language Models (LLMs) for Retrieval-Augmented Generation (RAG) search functionalities. It enables users to parse and visualize topics discussed in Telegram chats and find relevant information based on queries using Elastic Search.

## Problem Description
Standard search in Telegram some times does not work well. It
 - is not able to use semantic search
 - is not able to do summarization of search results
 - is not considering parent child relation in the chat messages. Thus, if somebody asks "Please recommend plumber in our city?" and it anybody else replies later, when I next time do a search by 'plumber', I'm able to find only the first, topic-starting message, while the information that is interesting for me, the phone of the plumber is somewhere in one of the related child topic messages.

## RAG based search over Telegram Messages
Features:
- retrieving of Telegram messages from exported data or directly though Telegram API
- Creation of  an in-memory index of Telegram messages.
- Building of "Topic tree" from these messages, using LLM
- Visualize topic trees from messages using graph representations.
- Summarization of data in such topics, using LLM
- Translation of messages from the chat to English for better dense vector embedding
- Indexing of that data in Elastic Search
- Search over that data using both simple search and semantic (vector embedding) search
- RAG, - Answering of users questions, using combination of Elastic Search to retrieve potentially relevant data, feeding that to LLM (OpenAI) that should ultimately evaluate the relevance of data and provide the answer

You can check main features from the list above in this [notebook](telegram_llm_playing_around.ipynb)
or by playing around with [tests](tests.py).
### Technologies been used
- Elastic Search for search over text data
- Open AI for summarization of the messages
- SentenceTranformer for calculation of RAG embedding-s
- graphviz  Digraph for visualization of graphs (Discussion tree)
- Docker for launching of Elastic Search
  
### Implementation details
- Unfortunatly, I could not find any SentenceTransformer model, that might work reliably create vector embedding  with Russian text.
You can take a look at  [Cousine similarity comparison notebook](cousine_similarity.ipynb), where I tried to compare different models for calculations of vector embedding.
So, for search over russian messages I'm using simple ES search by tags, so that firstly we are requesting ES by tags, than passing the questions and the doucmements we have recieved from ES to LLM
- For applying of standard RAG schema (dense vector cousine similarity search plus LLM) over russian languages I had to translate these messages to English first and push it to separate index.
- Also for search I'm using another approach. I'm grouping the messages into topics. As as first level of this grouping I use explicit links of the messages to each other, building discussion tree, that looks like this.
![image](https://github.com/user-attachments/assets/8206dc68-1971-47d5-b849-e3d29c6cf907)
But as not of the messages are linked to each other explicitly, I have to extend this list by adding adjacent messages and feed this to LLM to sort out who is relevant and to create document with topic summary,both in Russian and in English. This document is pushed to ES, where it can be used for vector search by English fields later.
- to make grouping messages in topics faster I've created kind of self-made in-memory index class [telegram_messages_index](src/telegram_messages_index.py). To understand how it works refer to tests.
![image](https://github.com/user-attachments/assets/e76e1565-cfcb-4187-8457-eeccedb14e02)

- for configuring of ES indexes I'm using [yml files like this](src/elastic_search/index_settings.yml)

### Not implemented yet, but in plans
- Add evaluation of RAG search
- Make from this telegram bot, or\and make Streamlit application as UI. 
- create ETL for pulling the new messages from the chat and pushing the documents to ES index
- 


