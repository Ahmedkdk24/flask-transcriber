import os
import requests

# Kaggle tunnel URL (set in your environment)
KAGGLE_URL = os.environ.get("KAGGLE_NGROK_URL")

# Path to static folder (relative to your project root)
STATIC_FOLDER = os.path.join(os.getcwd(), "static")

os.makedirs(STATIC_FOLDER, exist_ok=True)

def send_to_kaggle(filepath, language="en"):
    if not KAGGLE_URL:
        return {"error": "KAGGLE_NGROK_URL not set"}

    try:
        with open(filepath, "rb") as infile:
            r = requests.post(
                f"{KAGGLE_URL}/transcribe",
                files={"file": infile},
                data={"language": language},
                timeout=1200,
                verify=False
            )

        if r.status_code != 200:
            return {"error": f"Kaggle server error: {r.text}"}

        # Kaggle responds with a transcript.txt file (plain text)
        transcript_text = r.content.decode("utf-8", errors="ignore")

        # Save the file into /static/ so Flask can serve it
        output_filename = "transcript.txt"
        output_path = os.path.join(STATIC_FOLDER, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)

        return {
            "text": transcript_text,
            "download_filename": output_filename
        }

    except requests.RequestException as e:
        print(f"❌ Error contacting Kaggle server: {e}")
        return {"error": f"Error contacting Kaggle server: {e}"}