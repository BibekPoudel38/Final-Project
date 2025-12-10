import os
from google import genai
import dotenv

dotenv.load_dotenv(r"c:\Users\poude\Documents\Final Project\backend\bizai\.env")

try:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    print("Available methods in client.models:")
    print([m for m in dir(client.models) if not m.startswith("_")])
except Exception as e:
    print(e)
