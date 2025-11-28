# GraphQL Agent

Dynamic LLM agent that introspects your GraphQL schema and generates queries automatically.

## Quick Start

1. **Configure** - Edit `config.py`:
   ```python
   GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"
   ```

2. **Install**:
   ```bash
   pip install flask langchain-ollama langchain-core requests
   ```

3. **Run**:
   ```bash
   python app.py
   ```

4. **Use**:
   ```bash
   curl -X POST http://localhost:5000/chat \
     -H "Content-Type: application/json" \
     -d '{"query": "Show me all inventory items"}'
   ```

## How It Works

The agent:
1. **Introspects** your GraphQL schema to discover available queries
2. **Generates** appropriate GraphQL queries based on user questions
3. **Executes** queries and returns natural language responses

## Tools

- `introspect_schema()` - Discovers available queries/mutations
- `query_graphql(query)` - Executes any GraphQL query
- `query_inventory(action, ...)` - Common inventory operations
- `query_suppliers(action, ...)` - Common supplier operations

## Examples

```bash
# List inventory
curl -X POST http://localhost:5000/chat \
  -d '{"query": "Show me all inventory items"}'

# Search
curl -X POST http://localhost:5000/chat \
  -d '{"query": "Find items named widget"}'

# Low stock
curl -X POST http://localhost:5000/chat \
  -d '{"query": "What items are low in stock?"}'

# Suppliers
curl -X POST http://localhost:5000/chat \
  -d '{"query": "List all suppliers"}'

# Sales Trends
curl -X POST http://localhost:5000/chat \
  -d '{"query": "Show me sales trends for last month"}'

# Sales Metrics
curl -X POST http://localhost:5000/chat \
  -d '{"query": "What is the total revenue?"}'
```

## Files

- `config.py` - Configuration
- `agent.py` - GraphQL agent with tools
- `app.py` - Flask API server
- `README.md` - This file
