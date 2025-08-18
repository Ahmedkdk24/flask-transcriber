import os
from dotenv import load_dotenv

load_dotenv()  # Make sure your .env file is in the same folder

NGROK_URL = os.getenv("KAGGLE_NGROK_URL")
print(f"NGROK_URL: {NGROK_URL}")
