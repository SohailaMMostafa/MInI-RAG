# Mini-RAG: Multilingual Retrieval-Augmented Generation

A modular, API-based RAG (Retrieval-Augmented Generation) system for question answering over your own documents. Upload files into separate projects, process them into searchable chunks, and ask questions in **Arabic or English** to get answers grounded in your data.

> **Status:** In progress. The backend is working end to end. A web interface, quality and speed improvements, and deployment are planned.

## Features

- **Multiple document collections:** every upload belongs to a project ID, so you can keep separate knowledge bases.
- **Document processing:** files are split into chunks and stored in MongoDB.
- **Vector search:** chunk embeddings are indexed in the Qdrant vector database for semantic search per project.
- **Interchangeable LLM providers:** OpenAI and Cohere are supported for both embeddings and answer generation.
- **Grounded answers:** the most relevant chunks are retrieved for a query and passed to the LLM to generate the answer.
- **Bilingual:** works with Arabic and English documents and queries.
- **REST API:** built with FastAPI, with interactive documentation included.

## How It Works

```
Upload files  ->  Process into chunks  ->  Embed and index in Qdrant  ->  Semantic search  ->  LLM answer
```

1. **Upload:** send your documents to the upload API and receive them under a project ID.
2. **Process:** the processing API reads a project's documents, splits them into chunks, and saves the chunks in MongoDB.
3. **Index:** the vector database API embeds the chunks and pushes them into Qdrant for that project.
4. **Search and answer:** send a query with a project ID. The system retrieves the most relevant chunks and generates an answer with the selected LLM provider.

## Tech Stack

Python, FastAPI, MongoDB, Qdrant, OpenAI API, Cohere API, Docker

## Requirements

- Python 3.14.8 or later
- Docker and Docker Compose
- An OpenAI and/or Cohere API key

### Install Python using MiniConda

1. Download and install MiniConda from [here](https://docs.anaconda.com/free/miniconda/index.html).
2. Create a new environment:

```bash
conda create -n mini-rag python=3.14.8
```

3. Activate the environment:

```bash
conda activate mini-rag
```

## Installation

### Install the required packages

```bash
pip install -r requirements.txt
```

### Set up the environment variables

```bash
cp .env.example .env
```

Set your environment variables in the `.env` file, such as `OPENAI_API_KEY` and `COHERE_API_KEY`.

## Run Docker Compose Services

```bash
cd docker
cp .env.example .env
```

Update `.env` with your credentials, then start the services:

```bash
cd docker
sudo docker compose up -d
```

## Run the FastAPI Server

```bash
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`. Open `http://localhost:8000/docs` for the interactive Swagger documentation, where you can try every endpoint (upload, process, index, search, and answer).

## Roadmap

- [ ] Web interface for chatting with the model
- [ ] Improve answer quality and retrieval accuracy
- [ ] Improve response speed
- [ ] Deployment

## Author

**Sohaila Mostafa** | [GitHub](https://github.com/SohailaMMostafa) | [LinkedIn](https://www.linkedin.com/in/sohailaamostafaa/)
