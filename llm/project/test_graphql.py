import requests
import json

# Test with supplier as a string field
query = """
query { 
    allInventory { 
        edges { 
            node { 
                id 
                itemName 
                quantity 
                quantityUnit 
                type 
                sellingPrice 
                costPrice 
                supplier
            } 
        } 
    } 
}
"""

response = requests.post(
    "http://localhost:8000/graphql/",
    json={"query": query},
    headers={"Content-Type": "application/json"},
)

print("Status Code:", response.status_code)
print("\nResponse:")
result = response.json()
print(json.dumps(result, indent=2))

if "data" in result and result["data"]:
    items = result["data"]["allInventory"]["edges"]
    print(f"\n✅ SUCCESS! Found {len(items)} items")
