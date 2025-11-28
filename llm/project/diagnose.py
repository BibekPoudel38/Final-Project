"""
Quick script to test GraphQL endpoint and see actual schema
"""

import requests
import json

ENDPOINT = "http://localhost:8000/graphql/"

# Test 1: Introspect schema
print("=" * 60)
print("Testing Schema Introspection")
print("=" * 60)

introspection_query = """
{
    __schema {
        queryType { name }
        types {
            name
            kind
            fields {
                name
            }
        }
    }
}
"""

try:
    response = requests.post(ENDPOINT, json={"query": introspection_query}, timeout=10)
    result = response.json()

    if "data" in result:
        schema = result["data"]["__schema"]
        query_type_name = schema["queryType"]["name"]

        # Find the Query type
        query_type = next(
            (t for t in schema["types"] if t["name"] == query_type_name), None
        )

        if query_type and query_type.get("fields"):
            print(f"\n✅ Available Queries ({len(query_type['fields'])}):")
            for field in query_type["fields"]:
                print(f"  - {field['name']}")
        else:
            print("\n❌ No query fields found")

    elif "errors" in result:
        print(f"\n❌ GraphQL Errors:")
        for error in result["errors"]:
            print(f"  - {error.get('message', error)}")

    else:
        print(f"\n❌ Unexpected response: {result}")

except Exception as e:
    print(f"\n❌ Error: {e}")

# Test 2: Try a simple query
print("\n" + "=" * 60)
print("Testing Simple Inventory Query")
print("=" * 60)

# Try different possible query names
test_queries = [
    "query { allInventory { edges { node { id } } } }",
    "query { inventories { edges { node { id } } } }",
    "query { inventory { edges { node { id } } } }",
]

for test_query in test_queries:
    print(f"\nTrying: {test_query[:50]}...")
    try:
        response = requests.post(ENDPOINT, json={"query": test_query}, timeout=10)
        result = response.json()

        if "data" in result and not result.get("errors"):
            print(f"  ✅ Success!")
            print(f"  Response: {json.dumps(result, indent=2)[:200]}...")
            break
        elif "errors" in result:
            print(f"  ❌ Error: {result['errors'][0].get('message', 'Unknown error')}")
    except Exception as e:
        print(f"  ❌ Exception: {e}")
