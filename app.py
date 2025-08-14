from flask import Flask, request, render_template, send_file, jsonify
import os, uuid, tempfile
from gcp_control import start_gpu_vm
from config import GCS_BUCKET
from google.cloud import storage
from pydub import AudioSegment
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'wav', 'mp3'}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        audio_file = request.files.get('file')
        if not audio_file:
            return jsonify({"error": "No file uploaded."}), 400
        if not allowed_file(audio_file.filename):
            return jsonify({"error": "Invalid file type. Only .wav and .mp3 allowed."}), 400
        audio_file.seek(0, os.SEEK_END)
        file_size = audio_file.tell()
        audio_file.seek(0)
        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": "File too large. Max 200MB allowed."}), 400
        try:
            filename = secure_filename(audio_file.filename)
            job_id = str(uuid.uuid4())
            ext = os.path.splitext(filename)[1].lower()
            local_path = os.path.join(tempfile.gettempdir(),f"{job_id}.wav")

            # Convert mp3 to wav if needed
            if ext == ".mp3":
                mp3_path = os.path.join(tempfile.gettempdir(),f"{job_id}.mp3")
                audio_file.save(mp3_path)
                audio = AudioSegment.from_mp3(mp3_path)
                audio.export(local_path, format="wav")
                os.remove(mp3_path)
            else:
                audio_file.save(local_path)

            # Start GPU VM
            instance = start_gpu_vm()
            if not instance:
                return jsonify({"error": "Could not start any GPU VM from fallback list."}), 500

            # Upload to GCS
            storage_client = storage.Client()
            bucket = storage_client.bucket(GCS_BUCKET)
            blob = bucket.blob(f"jobs/{job_id}/input.wav")
            blob.upload_from_filename(local_path)

            # Write initial status file (queued)
            status_blob = bucket.blob(f"status/{job_id}.txt")
            status_blob.upload_from_string("status:queued", content_type="text/plain")

            return jsonify({
                "message": "Job submitted.",
                "job_id": job_id,
                "status_url": f"/status/{job_id}",
                "download_url": f"/download/{job_id}"
            }), 202
        except Exception as e:
            return jsonify({"error": f"Internal server error: {str(e)}"}), 500
    return render_template('index.html')

@app.route('/status/<job_id>', methods=['GET'])
def status(job_id):
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    status_blob = bucket.blob(f"status/{job_id}.txt")
    result_blob = bucket.blob(f"results/{job_id}/output.txt")
    if status_blob.exists():
        status_content = status_blob.download_as_text()
        status_lines = status_content.splitlines()
        status_dict = {}
        for line in status_lines:
            if ':' in line:
                k, v = line.split(':', 1)
                status_dict[k.strip()] = v.strip()
        # If job is done, add download URL
        if result_blob.exists():
            status_dict["download_url"] = f"/download/{job_id}"
        return jsonify(status_dict)
    elif result_blob.exists():
        return jsonify({"status": "completed", "download_url": f"/download/{job_id}"})
    else:
        return jsonify({"status": "not_found", "error": "Job ID not found."}), 404

@app.route('/download/<job_id>', methods=['GET'])
def download(job_id):
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    result_blob = bucket.blob(f"results/{job_id}/output.txt")
    if result_blob.exists():
        tmp_path = os.path.join(tempfile.gettempdir(),f"{job_id}.txt")
        result_blob.download_to_filename(tmp_path)
        return send_file(tmp_path, as_attachment=True)
    else:
        return jsonify({"error": "Result not ready yet"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)