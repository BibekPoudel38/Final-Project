import requests
import json
from formatter import ResponseFormatter

# Configuration
ENDPOINT = "http://localhost:8000/graphql/"


def test_query(name, query, variables=None):
    print(f"\n{'='*20} TEST: {name} {'='*20}")
    try:
        response = requests.post(
            ENDPOINT,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if "errors" in result:
                print("❌ GraphQL Errors:", json.dumps(result["errors"], indent=2))
            else:
                data = result.get("data", {})
                print("✅ Query Successful")

                # Test Formatter
                print("\n--- Formatter Output ---")
                formatted = ResponseFormatter.analyze_and_format(
                    result, f"Test query for {name}"
                )
                print(f"Display Type: {formatted['display_type']}")
                print("Metadata:", json.dumps(formatted["metadata"], indent=2))

                if "allSales" in data:
                    count = len(data["allSales"]["edges"])
                    print(f"Found {count} sales records")
        else:
            print("❌ Request Failed:", response.text)

    except Exception as e:
        print(f"❌ Exception: {e}")


# 1. Basic Sales Query
query_basic = """
query {
  allSales(first: 5) {
    edges {
      node {
        id
        saleDate
        revenue
        quantitySold
        weatherCondition
        prodId {
          itemName
          category
        }
      }
    }
  }
}
"""

# 2. Filtered Query (Revenue & Weather)
query_filtered = """
query {
  allSales(
    minRevenue: 100.0,
    weatherCondition: "Sunny",
    first: 5
  ) {
    edges {
      node {
        saleDate
        revenue
        weatherCondition
        prodId {
          itemName
        }
      }
    }
  }
}
"""

# 3. Metrics Query (for formatter testing)
query_metrics = """
query {
  allSales(first: 50) {
    edges {
      node {
        revenue
        quantitySold
        promotionType
      }
    }
  }
}
"""

if __name__ == "__main__":
    print("🚀 Starting Sales Integration Tests...")
    test_query("Basic Sales List", query_basic)
    test_query("Filtered Sales (Sunny, >$100)", query_filtered)
    test_query("Sales Metrics", query_metrics)

    # Mock Test for Formatter Verification
    print("\n" + "=" * 20 + " MOCK TEST " + "=" * 20)
    mock_data = {
        "data": {
            "allSales": {
                "edges": [
                    {
                        "node": {
                            "id": "1",
                            "saleDate": "2023-10-25",
                            "revenue": 150.00,
                            "quantitySold": 5,
                            "weatherCondition": "Sunny",
                            "promotionType": "None",
                            "prodId": {"itemName": "Widget A", "category": "Widgets"},
                        }
                    },
                    {
                        "node": {
                            "id": "2",
                            "saleDate": "2023-10-26",
                            "revenue": 200.00,
                            "quantitySold": 8,
                            "weatherCondition": "Cloudy",
                            "promotionType": "Summer",
                            "prodId": {"itemName": "Widget B", "category": "Widgets"},
                        }
                    },
                ]
            }
        }
    }

    print("Testing Formatter with Mock Data...")
    formatted = ResponseFormatter.analyze_and_format(mock_data, "Show me sales metrics")
    print("\nDisplay Type:", formatted["display_type"])
    print("Data:", json.dumps(formatted["data"], indent=2))

    formatted_chart = ResponseFormatter.analyze_and_format(
        mock_data, "Show me sales trend"
    )
    print("\nDisplay Type:", formatted_chart["display_type"])
    print("Data:", json.dumps(formatted_chart["data"], indent=2))

    formatted_table = ResponseFormatter.analyze_and_format(mock_data, "List sales")
    print("\nDisplay Type:", formatted_table["display_type"])
    print("Data:", json.dumps(formatted_table["data"], indent=2))
