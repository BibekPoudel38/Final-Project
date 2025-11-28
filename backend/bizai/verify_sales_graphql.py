import requests
import json


def run_query(query):
    url = "http://127.0.0.1:8000/graphql/"
    response = requests.post(url, json={"query": query})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(
            f"Query failed to run by returning code of {response.status_code}. {query}"
        )


def verify():
    # 1. Query all sales
    query_all = """
    query {
        allSales(first: 5) {
            edges {
                node {
                    salesUid
                    revenue
                    quantitySold
                }
            }
        }
    }
    """
    print("Running allSales query...")
    try:
        result = run_query(query_all)
        print("Result:", json.dumps(result, indent=2))
        if "errors" in result:
            print("Errors found!")
            return False
    except Exception as e:
        print(f"Failed: {e}")
        return False

    # 2. Query sales holidays
    query_holidays = """
    query {
        allSalesHolidays(first: 5) {
            edges {
                node {
                    name
                    date
                }
            }
        }
    }
    """
    print("\nRunning allSalesHolidays query...")
    try:
        result = run_query(query_holidays)
        print("Result:", json.dumps(result, indent=2))
        if "errors" in result:
            print("Errors found!")
            return False
    except Exception as e:
        print(f"Failed: {e}")
        return False

    return True


if __name__ == "__main__":
    if verify():
        print("\nVerification Successful!")
    else:
        print("\nVerification Failed!")
