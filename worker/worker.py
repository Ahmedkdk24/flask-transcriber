import time, os, threading, logging
from google.cloud import storage
from config import GCS_BUCKET, POLL_INTERVAL, PROJECT, TMP_DIR
from transcribe import transcribe_audio

# Setup logging for info and error messages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Initialize Google Cloud Storage client and bucket
storage_client = storage.Client()
bucket = storage_client.bucket(GCS_BUCKET)

def cleanup_file(path):
    """
    Remove temporary file from local disk.
    """
    try:
        if os.path.exists(path):
            os.remove(path)
            logging.info(f"Cleaned up temporary file: {path}")
    except Exception as e:
        logging.warning(f"Failed to clean up {path}: {e}")

def update_status(job_id, status, error_msg=None):
    """
    Update job status in GCS for tracking progress.
    """
    status_blob = bucket.blob(f"status/{job_id}.txt")
    status_content = f"status:{status}"
    if error_msg:
        status_content += f"\nerror:{error_msg}"
    status_blob.upload_from_string(status_content, content_type="text/plain")

def process_job(blob):
    """
    Download audio file, transcribe it, upload result, update status, and clean up.
    """
    job_id = blob.name.split("/")[1]
    local_path = os.path.join(TMP_DIR, f"{job_id}.wav")
    try:
        logging.info(f"▶ Processing job {job_id}...")
        update_status(job_id, "processing")
        blob.download_to_filename(local_path)  # Download audio from GCS

        # Define a progress callback that captures job_id
        def progress_callback(current, total):
            percent = int((current / total) * 100)
            status_blob = bucket.blob(f"status/{job_id}.txt")
            status_content = f"status:processing\nprogress:{percent}"
            status_blob.upload_from_string(status_content, content_type="text/plain")
            logging.info(f"Job {job_id} progress: {percent}% ({current}/{total})")

        text_output = transcribe_audio(local_path, progress_callback=progress_callback)  # Run transcription

        # Upload transcription result to GCS
        result_blob = bucket.blob(f"results/{job_id}/output.txt")
        result_blob.upload_from_string(text_output, content_type="text/plain")
        update_status(job_id, "done")
        logging.info(f"✅ Job {job_id} completed.")
        blob.delete()  # Remove job file from GCS
    except Exception as e:
        logging.error(f"❌ Job {job_id} failed: {e}")
        update_status(job_id, "failed", str(e))
    finally:
        cleanup_file(local_path)  # Always clean up temp file

    """
    Download audio file, transcribe it, upload result, update status, and clean up.
    """
    job_id = blob.name.split("/")[1]
    local_path = os.path.join(TMP_DIR, f"{job_id}.wav")
    try:
        logging.info(f"▶ Processing job {job_id}...")
        update_status(job_id, "processing")
        blob.download_to_filename(local_path)  # Download audio from GCS
        text_output = transcribe_audio(local_path, progress_callback=progress_callback)  # Run transcription

        # Upload transcription result to GCS
        result_blob = bucket.blob(f"results/{job_id}/output.txt")
        result_blob.upload_from_string(text_output, content_type="text/plain")
        update_status(job_id, "done")
        logging.info(f"✅ Job {job_id} completed.")
        blob.delete()  # Remove job file from GCS
    except Exception as e:
        logging.error(f"❌ Job {job_id} failed: {e}")
        update_status(job_id, "failed", str(e))
    finally:
        cleanup_file(local_path)  # Always clean up temp file

def process_jobs():
    """
    Poll for new jobs, process each in a separate thread, and wait for all to finish.
    """
    while True:
        blobs = list(bucket.list_blobs(prefix="jobs/"))
        threads = []
        for blob in blobs:
            if blob.name.endswith("input.wav"):
                job_id = blob.name.split("/")[1]
                # Skip jobs that are already processing or done
                status_blob = bucket.blob(f"status/{job_id}.txt")
                if status_blob.exists():
                    status = status_blob.download_as_text().split(":")[1].strip()
                    if status in ["processing", "done"]:
                        continue
                # Start a new thread for each job
                t = threading.Thread(target=process_job, args=(blob,))
                t.start()
                threads.append(t)
        # Wait for all threads to finish before polling again
        for t in threads:
            t.join()
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    # Ensure temp directory exists before starting
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)
    process_jobs()