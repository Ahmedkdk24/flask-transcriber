# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from services.kaggle_client import send_to_kaggle

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
ALLOWED_EXTENSIONS = {"wav", "mp3", "m4a", "ogg"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = "dev-secret"  # replace in production

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Validate upload
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash(f"File type not allowed: {file.filename}")
            return redirect(request.url)

        # Save locally
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Send to Kaggle
        result = send_to_kaggle(filepath)

        if "error" in result:
            # Render error clearly
            return render_template(
                "result.html",
                transcript=None,
                error=result["error"],
                download_url=None
            )
        else:
            kaggle_server_url = os.environ.get("KAGGLE_SERVER_URL", "")
            download_url = result.get("download_url")
            if download_url and kaggle_server_url:
                # Ensure no double slash
                if download_url.startswith("/"):
                    download_url = kaggle_server_url.rstrip("/") + download_url
                else:
                    download_url = kaggle_server_url.rstrip("/") + "/" + download_url
            return render_template(
                "result.html",
                transcript=result.get("text", ""),
                error=None,
                download_url=download_url
            )

    return render_template("index.html")


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=True)
