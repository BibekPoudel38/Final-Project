import requests
import json

# Test the fixed agent
response = requests.post(
    "http://localhost:5000/chat",
    json={"query": "Weekly sales report sorted by date"},
    headers={"Content-Type": "application/json"},
)

print("Status Code:", response.status_code)
print("\nResponse:")
result = response.json()
with open("debug_response.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

# Check if we got formatted data
if result.get("formatted_data"):
    print(f"\n✅ SUCCESS! Got formatted data:")
    print(f"  Display Type: {result['formatted_data']['display_type']}")
    if "data" in result["formatted_data"]:
        data = result["formatted_data"]["data"]
        if "rows" in data:
            print(f"  Rows: {len(data['rows'])}")
        if "columns" in data:
            print(f"  Columns: {len(data['columns'])}")
else:
    print("\n❌ FAILED - No formatted data")
    print(f"Answer: {result.get('answer', '')[:200]}")
    if "error" in result:
        print(f"Error Details: {result['error']}")

print(f"\nLogs: {result.get('logs', [])}")
