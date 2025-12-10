import sys
import os

# Create mock Flask app context if needed
from flask import Flask

app = Flask(__name__)

# Mock config
import config

# Mock requests.post/get if needed, OR just let it hit the real backend
# Assuming backend is running on localhost:8000

from agent import GraphQLAgent

# Add proper python path if needed
sys.path.append(os.getcwd())


def test_crash():
    agent = GraphQLAgent()
    print("Testing ask('Sales trend for 2025')...")

    # We need to simulate the request_token context var if we want auth to work
    # But for reproducing the crash, maybe it crashes even without it?
    # Or strict auth check?

    from agent import request_token

    token = request_token.set("Bearer MAGIC_TEST_TOKEN")

    try:
        response = agent.ask("Sales trend for 2025 December")
        print("Response:", response)
    finally:
        request_token.reset(token)


if __name__ == "__main__":
    with app.app_context():
        test_crash()
