import requests
import json
import os
import random
import string

# Configuration
BASE_URL = "http://localhost:8000"
ONBOARDING_URL = f"{BASE_URL}/api/merchant/onboarding/"


def get_random_string(length=8):
    return "".join(random.choices(string.ascii_lowercase, k=length))


# Test Data
rand_str = get_random_string()
USER_PROFILE = {
    "name": f"Test User {rand_str}",
    "email": f"test_{rand_str}@example.com",
    "phone_number": "+1234567890",
}

BUSINESS_PROFILE = {
    "business_name": f"Test Business {rand_str}",
    "business_email": f"business_{rand_str}@example.com",
    "business_phone": "+1987654321",
    "industry": "retail",
    "address": {
        "street": "123 Test St",
        "city": "Test City",
        "state": "TS",
        "zip_code": "12345",
        "country": "Testland",
    },
}

SOCIAL_PROFILES = [
    {
        "platform": "Instagram",
        "profile_url": "https://instagram.com/test",
        "active": True,
        "media_type": "image",
    }
]


def create_dummy_csv():
    filename = f"test_sales_{get_random_string()}.csv"
    content = "date,product_name,revenue,quantity_sold\n2023-01-01,Widget A,100.0,10\n2023-01-02,Widget B,200.0,5"
    with open(filename, "w") as f:
        f.write(content)
    return filename


def run_test():
    # 1. Skip Login - Use Magic Token
    # Note: Backend needs to handle dynamic user creation for magic token if we want unique users
    # But our magic token implementation returns a fixed email "test_user@example.com".
    # So we are stuck with that user.
    # We need to DELETE the previous data for this user if we want to retry.
    # OR, we modify supabase_auth.py to accept the email in the token? No, token is opaque.

    # Let's try to use a NEW magic token format: "MAGIC:email"
    print("Using Magic Token...")
    email = f"test_{get_random_string()}@example.com"
    token = f"MAGIC:{email}"

    # Update payload to match token email
    USER_PROFILE["email"] = email

    # 2. Prepare Onboarding Data
    payload = {
        "userProfile": USER_PROFILE,
        "businessProfile": BUSINESS_PROFILE,
        "socialProfiles": SOCIAL_PROFILES,
    }

    csv_file = create_dummy_csv()

    # Open file safely
    with open(csv_file, "rb") as f_obj:
        files = {"file": (csv_file, f_obj, "text/csv")}
        data = {"data": json.dumps(payload)}
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Send Onboarding Request
        print(f"Sending onboarding request for {email}...")
        try:
            resp = requests.post(
                ONBOARDING_URL, headers=headers, data=data, files=files
            )

            print(f"Response Status: {resp.status_code}")
            print(f"Response Text: {resp.text}")

            # 4. Verify Completion Status
            print("Verifying completion status...")
            get_resp = requests.get(ONBOARDING_URL, headers=headers)
            print(f"GET Status: {get_resp.status_code}")
            print(f"GET Response: {get_resp.text}")

        except Exception as e:
            print(f"Request failed: {e}")

    # Cleanup
    if os.path.exists(csv_file):
        os.remove(csv_file)


if __name__ == "__main__":
    run_test()
