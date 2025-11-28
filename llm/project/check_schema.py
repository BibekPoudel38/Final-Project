"""
Simple test to check what GraphQL queries your Django backend actually supports
Run this to see your actual schema
"""

import requests
import json

ENDPOINT = "http://localhost:8000/graphql/"

print("🔍 Discovering your GraphQL schema...\n")

# Get schema
introspection = """
{
    __schema {
        queryType { name }
        types {
            name
            fields { name }
        }
    }
}
"""

response = requests.post(ENDPOINT, json={"query": introspection})
result = response.json()

if "data" in result:
    schema = result["data"]["__schema"]
    query_type_name = schema["queryType"]["name"]
    query_type = next(
        (t for t in schema["types"] if t["name"] == query_type_name), None
    )

    print("✅ Available GraphQL Queries:")
    print("=" * 60)
    if query_type:
        for field in query_type.get("fields", []):
            print(f"  • {field['name']}")
    print("\n")

# Now test the actual queries
print("🧪 Testing inventory queries...\n")

test_cases = [
    (
        "All Inventory",
        "query { allInventory { edges { node { id itemName quantity } } } }",
    ),
    (
        "Low Stock (if exists)",
        "query { lowStockInventory { edges { node { id itemName quantity minQuantity } } } }",
    ),
]

for name, query in test_cases:
    print(f"Testing: {name}")
    print(f"Query: {query[:80]}...")

    response = requests.post(ENDPOINT, json={"query": query})
    result = response.json()

    if "data" in result and not result.get("errors"):
        print(f"  ✅ Works!")
        print(f"  Data: {json.dumps(result['data'], indent=2)[:300]}...\n")
    elif "errors" in result:
        print(f"  ❌ Error: {result['errors'][0]['message']}\n")
    else:
        print(f"  ❌ Unexpected response\n")
