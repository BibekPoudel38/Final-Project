from agent import GraphQLAgent
import json

print("🚀 Starting Direct Agent Debug...")

try:
    agent = GraphQLAgent()
    print("✅ Agent initialized")

    query = "Inventory report"
    print(f"\nAsking: {query}")

    result = agent.ask(query)

    print("\n--- Result ---")
    print(json.dumps(result, indent=2))

    if "logs" in result:
        print("\n--- Logs ---")
        for log in result["logs"]:
            print(log)

except Exception as e:
    print(f"\n❌ Exception: {e}")
    import traceback

    traceback.print_exc()
