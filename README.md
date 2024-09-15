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
or by playing around with [tests](tests.py)


