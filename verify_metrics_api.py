import requests
import json
import sys
import time

# Configuration
API_URL = "http://localhost:8000/api/sales/metrics/"
TRAIN_URL = "http://localhost:8000/api/sales/train/"


def verify_metrics():
    print("1. Triggering Training to populate metrics...")
    try:
        # Trigger training
        print(f"POSTing to {TRAIN_URL}...")
        train_response = requests.post(TRAIN_URL)
        if train_response.status_code == 200:
            print("Training triggered successfully.")
            # print(json.dumps(train_response.json(), indent=2))
        else:
            print(f"Training failed. Status: {train_response.status_code}")
            print(train_response.text)

        # Fetch metrics
        print(f"\n2. Fetching metrics from {API_URL}...")
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            print("Response received:")
            print(json.dumps(data, indent=2))

            if "training_info" in data:
                print("\nSUCCESS: 'training_info' field is present.")
            else:
                print("\nFAILURE: 'training_info' field is MISSING.")
        else:
            print(f"Failed to fetch metrics. Status: {response.status_code}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Wait a bit for data gen to finish if running in parallel (though we are sequential here)
    verify_metrics()
