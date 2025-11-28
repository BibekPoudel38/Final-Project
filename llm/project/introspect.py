import requests
import json

# Introspect the GraphQL schema
introspection_query = """
query IntrospectionQuery {
  __schema {
    types {
      name
      kind
      fields {
        name
        type {
          name
          kind
          ofType {
            name
            kind
          }
        }
      }
    }
  }
}
"""

response = requests.post(
    "http://localhost:8000/graphql/",
    json={"query": introspection_query},
    headers={"Content-Type": "application/json"},
)

# Find the InventoryNode type
data = response.json()
for type_info in data["data"]["__schema"]["types"]:
    if type_info["name"] == "InventoryNode":
        print("InventoryNode fields:")
        for field in type_info["fields"] or []:
            print(f"  - {field['name']}: {field['type']}")
