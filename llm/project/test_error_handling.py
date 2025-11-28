import requests
import json

print("🚀 Testing Error Handling...")

# This query requests 'customerName' which does not exist
bad_query = "query { allSales(first: 1) { edges { node { revenue customerName } } } }"

response = requests.post(
    "http://localhost:5000/debug",  # Use debug endpoint to bypass agent logic and test execute_graphql directly
    json={"query": bad_query},
    headers={"Content-Type": "application/json"},
)

print(f"Status Code: {response.status_code}")
result = response.json()
print("\nResult:")
print(json.dumps(result, indent=2))

if "error" in result and "GraphQL Validation Error" in result["error"]:
    print("\n✅ SUCCESS: Got specific GraphQL validation error.")
    print("Details:", result.get("details"))
else:
    print("\n❌ FAILED: Did not get specific validation error.")
