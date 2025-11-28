import os

# Configuration
GRAPHQL_ENDPOINT = os.getenv("GRAPHQL_ENDPOINT", "http://localhost:8000/graphql/")
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://localhost:8000/api/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
