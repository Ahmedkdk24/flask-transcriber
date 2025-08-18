# services/kaggle_client.py
import os
import requests

KAGGLE_SERVER = os.environ.get("KAGGLE_SERVER_URL", "http://127.0.0.1:5000")

def send_to_kaggle(filepath):
    try:
        with open(filepath, "rb") as f:
            res = requests.post(f"{KAGGLE_SERVER}/transcribe", files={"file": f})

        if res.status_code != 200:
            return {"error": f"Kaggle server error {res.status_code}: {res.text}"}

        data = res.json()

        # Save transcript to static/transcript.txt (local side)
        if "text" in data:
            static_dir = os.path.join(os.getcwd(), "static")
            os.makedirs(static_dir, exist_ok=True)
            out_path = os.path.join(static_dir, "transcript.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(data["text"])
            data["local_download"] = "/static/transcript.txt"

        return data

    except requests.RequestException as e:
        print(f"❌ Error contacting Kaggle server: {e}")
        return {"error": f"Error contacting Kaggle server: {e}"}