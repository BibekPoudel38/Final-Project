"""
Flask API for GraphQL Agent
"""

from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
from agent import GraphQLAgent
import config

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
agent = GraphQLAgent()


@app.route("/", methods=["GET"])
def home():
    """API information."""
    return jsonify(
        {
            "status": "online",
            "endpoints": {
                "/": "GET - This info",
                "/chat": 'POST - Ask questions (JSON: {"query": "your question"})',
            },
            "examples": [
                "Show me all inventory items",
                "Search for items named 'widget'",
                "What items are low in stock?",
                "List all suppliers",
                "Show me sales trends for last month",
                "What is the total revenue?",
                "List top selling items",
                "Show sales on sunny days",
                "Draft a marketing email for new arrivals",
                "Explain the concept of ROI",
                "Write a thank you note to a customer",
            ],
        }
    )


@app.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.json
    user_query = data.get("query")
    session_id = data.get("session_id", "default")  # Get session_id or use default

    if not user_query:
        return jsonify({"error": "Missing 'query' field"}), 400

    result = agent.ask(user_query, session_id=session_id)
    return jsonify(result), 200


@app.route("/history", methods=["GET"])
def get_history():
    """Get chat history."""
    session_id = request.args.get("session_id", "default")
    try:
        url = f"{config.DJANGO_API_URL}chat/history/{session_id}/"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({"messages": []}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/clear_history", methods=["POST"])
def clear_history():
    """Clear conversation history for a session."""
    data = request.json if request.is_json else {}
    session_id = data.get("session_id", "default")

    agent.clear_history(session_id)
    return (
        jsonify(
            {
                "status": "success",
                "message": f"History cleared for session {session_id}",
            }
        ),
        200,
    )


@app.route("/debug", methods=["POST"])
def debug():
    """Debug endpoint to test raw GraphQL queries."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.json
    query = data.get("query")
    variables = data.get("variables")

    if not query:
        return jsonify({"error": "Missing 'query' field"}), 400

    from agent import execute_graphql

    result = execute_graphql(query, variables)
    return jsonify(result), 200


@app.route("/introspect", methods=["GET"])
def introspect():
    """Introspect the GraphQL schema."""
    from agent import introspect_schema

    result = introspect_schema.invoke({})
    return jsonify({"schema": result}), 200


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 GraphQL Agent API")
    print("=" * 60)
    print(f"Model: {config.OLLAMA_MODEL}")
    print(f"GraphQL: {config.GRAPHQL_ENDPOINT}")
    print(f"Port: {config.FLASK_PORT}")
    print("=" * 60 + "\n")

    app.run(host="0.0.0.0", port=config.FLASK_PORT, debug=True)
