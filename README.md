# Flask On-Demand GPU Transcription

## Overview
This project provides a Flask-based frontend to upload audio for transcription using Google Cloud GPUs **on demand**.

- CPU VM runs the Flask app
- Upload triggers GCS job creation and starts a GPU VM via fallback logic
- GPU VM runs `worker.py` to pull jobs, transcribe audio, and push results
- Auto shutdown of GPU VM can be added for cost control

## Setup
1. Create a GCP project, enable Compute Engine, Cloud Storage APIs.
2. Create a bucket, update `config.py` with `PROJECT`, `GCS_BUCKET`, and your VM fallback list.
3. Pre-create GPU VMs in listed zones, install CUDA, ffmpeg, Python deps.
4. Deploy `worker/` to GPU VMs.
5. Run `app.py` on CPU VM.

## Usage
- Open `/` in browser to upload audio
- Poll `/status/<job_id>` for progress
- Download results via `/download/<job_id>`
