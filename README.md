This project is an AI-powered shopping assistant that uses a Retrieval-Augmented Generation (RAG) framework to provide accurate, context-specific answers to user queries based on a product database.

Here are the core technologies used to build it:

Python: The primary programming language for the entire backend.

Flask: A lightweight web framework used to create the backend API and serve the web application's frontend.

LangChain: An orchestration framework that connects the different components of the RAG pipeline, from data loading to generating the final response.

Google Gemini API: Provides the Large Language Model (LLM) for generating human-like responses. The project uses models like gemini-1.5-flash.

ChromaDB: A vector database that stores the numerical representations (embeddings) of the product data, enabling fast and efficient semantic search.

Pandas: A data manipulation library used to read and process the product data from the CSV file.
