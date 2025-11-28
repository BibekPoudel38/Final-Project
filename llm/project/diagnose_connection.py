import requests
import sys
import json

# Configuration from config.py
try:
    import config

    ENDPOINT = config.GRAPHQL_ENDPOINT
except ImportError:
    ENDPOINT = "http://localhost:8000/graphql/"
    print("⚠️ Could not import config.py, using default:", ENDPOINT)


def test_connection(url):
    print(f"\nTesting connection to: {url}")
    try:
        # Simple introspection query
        query = """
        query {
            __schema {
                types {
                    name
                }
            }
        }
        """
        response = requests.post(
            url,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=5,
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("✅ Connection SUCCESSFUL!")
            try:
                data = response.json()
                if "data" in data:
                    print("✅ Valid GraphQL Response received.")
                    return True
                else:
                    print("⚠️ Response JSON does not contain 'data'.")
                    print(data)
            except json.JSONDecodeError:
                print("❌ Invalid JSON response.")
                print("Response text preview:", response.text[:200])
        else:
            print("❌ Server returned error status.")
            print("Response text preview:", response.text[:200])

    except requests.exceptions.ConnectionError:
        print("❌ Connection REFUSED. Is the server running on this port?")
    except Exception as e:
        print(f"❌ Error: {e}")

    return False


if __name__ == "__main__":
    print("🔍 GraphQL Connection Diagnostic Tool")
    print("=====================================")

    # 1. Test configured endpoint
    print(f"\nChecking configured endpoint: {ENDPOINT}")
    success = test_connection(ENDPOINT)

    if not success and "localhost" in ENDPOINT:
        # 2. Try 127.0.0.1 as fallback if localhost failed
        alt_url = ENDPOINT.replace("localhost", "127.0.0.1")
        print(f"\n⚠️ 'localhost' failed. Trying '127.0.0.1' instead: {alt_url}")
        test_connection(alt_url)

    print("\n=====================================")
    if success:
        print("🎉 Diagnostics passed. The agent should work.")
    else:
        print("🛑 Diagnostics failed. Please check:")
        print("1. Is the Django server running? (python manage.py runserver)")
        print("2. Is it running on port 8000?")
        print("3. Can you access the URL in your browser?")
