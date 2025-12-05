import requests
import json
import datetime
import random
import sys

# Configuration
API_URL = "http://localhost:8080/retrain"


def generate_dummy_data(days=100):
    data = []
    base_date = datetime.date(2025, 1, 1)
    items = ["item_A", "item_B"]

    for i in range(days):
        current_date = base_date + datetime.timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")

        for item in items:
            entry = {
                "date": date_str,
                "product_id": item,
                "sales_amount": round(random.uniform(100, 500), 2),
                "sales_quantity": random.randint(1, 20),
                "weather_condition": random.choice(["Sunny", "Rainy", "Cloudy"]),
                "temperature": round(random.uniform(10, 30), 1),
                "fuel_price": 4.5,
                "has_offers": random.choice([0, 1]),
                "offer_amount": random.choice([0, 10, 20]),
                "is_holiday": 0,
                "holidays_list": [],
                "festivals": [],
                "local_events": [],
            }
            data.append(entry)
    return data


def verify_retrain():
    print("Generating dummy data...")
    data = generate_dummy_data(days=100)

    payload = {"business_id": "test_biz_verify", "data": data}

    print(f"Sending POST request to {API_URL}...")
    try:
        response = requests.post(API_URL, json=payload)

        if response.status_code == 200:
            print("Request successful!")
            result = response.json()

            # Check Metrics
            metrics = result.get("metrics", {})
            print("\nMetrics:")
            print(json.dumps(metrics, indent=2))

            # Check Training Info
            training_info = result.get("training_info", {})
            print("\nTraining Info:")
            print(json.dumps(training_info, indent=2))

            # Verification Logic
            required_keys = [
                "train_start",
                "train_end",
                "test_start",
                "test_end",
                "split_ratio",
            ]
            missing_keys = [k for k in required_keys if k not in training_info]

            if missing_keys:
                print(f"\nFAILED: Missing keys in training_info: {missing_keys}")
                sys.exit(1)

            if training_info["split_ratio"] != "80/20":
                print(
                    f"\nFAILED: Incorrect split ratio: {training_info['split_ratio']}"
                )
                sys.exit(1)

            print("\nVERIFICATION PASSED: 80/20 split logic confirmed.")

        else:
            print(f"Request failed with status {response.status_code}")
            print(response.text)
            sys.exit(1)

    except Exception as e:
        print(f"Error connecting to API: {e}")
        sys.exit(1)


if __name__ == "__main__":
    verify_retrain()
