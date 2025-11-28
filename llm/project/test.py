"""
Quick test script for the GraphQL Agent
"""

import requests

API_URL = "http://localhost:5000"


def test_chat(query: str):
    """Send a test query."""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print("=" * 60)

    response = requests.post(
        f"{API_URL}/chat",
        json={"query": query},
        headers={"Content-Type": "application/json"},
    )

    result = response.json()
    print(f"\nAnswer: {result.get('answer', 'No answer')}")

    if result.get("logs"):
        print(f"\nLogs:")
        for log in result["logs"]:
            print(f"  - {log}")

    if result.get("error"):
        print(f"\nError: {result['error']}")

    print()


if __name__ == "__main__":
    print("\n🧪 Testing GraphQL Agent\n")

    # Test queries
    test_chat("Show me all inventory items")
    test_chat("What items are low in stock?")
    test_chat("Search for items named 'widget'")
    test_chat("List all suppliers")
