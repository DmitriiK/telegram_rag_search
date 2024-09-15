# LLM-Based RAG Search Over Telegram Messages

## Overview
This repository implements functionalities for retrieving and processing Telegram messages, specifically focusing on using Large Language Models (LLMs) for Retrieval-Augmented Generation (RAG) search functionalities. It enables users to parse and visualize topics discussed in Telegram chats and find relevant information based on queries using Elastic Search.

## RAG based search over Telegram Messages
Features:
- retrieving of Telegram messages from exported data or directrly though Telegram API
- Creation of  an in-memory index of Telegram messages.
- Building of "Topic tree" from these messages, using LLM
- Visualize topic trees from messages using graph representations.
- Summarization of data in such topics, using LLM
- Indexing of that data in Elastic Search
- Search over that data using both simple search and semantic (vector embedding) search
- RAG, - Answering of users questions, using combination of Elastic Search to retrieve potentially relevant data, feeding that to LLM (OpenAI) that should ultimately evaluate the relevance of data and provide the answer

You can check main features from the list above in this [notebook](telegram_llm_playing_around.ipynb)
or by playing around with [tests](tests.py).
### Technologies been used
- Elastic Search for search over text data
- Open AI for summarization of the messages
- SentenceTranformer for calculation of RAG embeddings
- graphviz  Digraph for vizualization of graphs (Discussion tree)
  
### Implementation details
Unfortunatly, I could not find any SentenceTransformer model, that might work reliably create vector embeddings  with russian text.
You can take a look at  [Cousine similarity comparison notebook](cousine_similarity.ipynb), where I tryid to compare different models for calculations of vector embeddings.
So, for search over messages I'm using simple ES search.
For semantic search I'm using another approach. I'm grouping the messages into topics. As as first level of this grouping I use explicit links of the messages to each other, building discussion tree, that looks like this.
![image](https://github.com/user-attachments/assets/8206dc68-1971-47d5-b849-e3d29c6cf907)
But as not of the messages are linked to each other explicitely, I have to extend this list by adding ajustent messages and feed this to LLM to sort out who is relevant and to create document with topic summary,both in russian and in english. This document is pushed to ES, where it can be used for vector search by English fields later.

### Not implemented yet, but in plans
- Add evaluation of RAG search
- Make from this telegram bot, or\and make Streamlit applicstion as UI.
- 


