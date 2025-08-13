from flask import Flask, request, render_template, send_file, jsonify
import os, uuid
from gcp_control import start_gpu_vm
from config import GCS_BUCKET
from google.cloud import storage

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        audio_file = request.files['file']
        if audio_file:
            job_id = str(uuid.uuid4())
            local_path = f"/tmp/{job_id}.wav"
            audio_file.save(local_path)

            # Start GPU VM
            instance = start_gpu_vm()
            if not instance:
                return "❌ Could not start any GPU VM from fallback list.", 500

            # Upload to GCS
            storage_client = storage.Client()
            bucket = storage_client.bucket(GCS_BUCKET)
            blob = bucket.blob(f"jobs/{job_id}/input.wav")
            blob.upload_from_filename(local_path)

            return f"✅ Job submitted. ID: {job_id}. Your transcription will be ready soon."
    return render_template('index.html')

@app.route('/status/<job_id>', methods=['GET'])
def status(job_id):
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    result_blob = bucket.blob(f"results/{job_id}/output.txt")
    if result_blob.exists():
        return jsonify({"status": "completed"})
    else:
        return jsonify({"status": "processing"})

@app.route('/download/<job_id>', methods=['GET'])
def download(job_id):
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    result_blob = bucket.blob(f"results/{job_id}/output.txt")
    if result_blob.exists():
        tmp_path = f"/tmp/{job_id}.txt"
        result_blob.download_to_filename(tmp_path)
        return send_file(tmp_path, as_attachment=True)
    else:
        return "❌ Result not ready yet", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
