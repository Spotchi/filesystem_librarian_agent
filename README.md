# Filesystem Librarian Agent

This is a [LlamaIndex](https://www.llamaindex.ai/) project bootstrapped with [`create-llama`](https://github.com/run-llama/LlamaIndexTS/tree/main/packages/create-llama) and instrumented using OpenInference.

## Overview

The Filesystem Librarian Agent is a simple application that allows you to chat with a librarian that can answer questions about a set of documents stored in a filesystem.

## Architecture Overview

- A NextJS frontend that provides an interface to a basic RAG chat application
- A Python FastAPI backend that serves a simple LlamaIndex RAG application. The LlamaIndex framework is instrumented using OpenInference to produce traces.
- A [Phoenix](https://github.com/Arize-ai/phoenix) server that acts as both a collector for OpenInference traces and as a trace UI for observability.



## Getting Started with Local Development

First, startup the backend as described in the [backend README](./backend/README.md).

- If you'd like, include your own data to build an index in [the data directory](./backend/data/)
- Build a simple index using LlamaIndex
- Ensure that your OpenAI API key is available to the application, either via the `OPENAI_API_KEY` environment variable or a `.env` file
- Start the backend server

Second, run the development server of the frontend as described in the [frontend README](./frontend/README.md).

Open [http://localhost:3000](http://localhost:3000) with your browser to use the chat interface to your RAG application.

Traces can be viewed using the [Phoenix UI](http://localhost:6006).

## Getting Started with Docker-Compose

1. If you'd like, add your own PDFs to `./backend/data` to build indexes over.
2. Follow the instructions in `backend/README.md` to install LlamaIndex using poetry and generate an index.
3. Ensure that your OpenAI API key is available to the application, either via the `OPENAI_API_KEY` environment variable or a `.env` file alongside `compose.yml`.
4. Ensure that Docker is installed and running.
5. Run the command `docker compose up --build` to spin up services for the frontend, backend, and Phoenix.
6. Once those services are running, open [http://localhost:3000](http://localhost:3000) to use the chat interface.
7. Traces can be viewed using the [Phoenix UI](http://localhost:6006).
8. When you're finished, run `docker compose down` to spin down the services.
