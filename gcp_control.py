from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from config import PROJECT, GPU_INSTANCE_ZONE, GPU_INSTANCE_NAME
import time

def start_gpu_vm():
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('compute', 'v1', credentials=credentials)

    try:
        status = service.instances().get(
            project=PROJECT,
            zone=GPU_INSTANCE_ZONE,
            instance=GPU_INSTANCE_NAME
        ).execute()

        if status['status'] != 'RUNNING':
            print(f"▶ Starting GPU VM: {GPU_INSTANCE_NAME} in {GPU_INSTANCE_ZONE}...")
            service.instances().start(
                project=PROJECT,
                zone=GPU_INSTANCE_ZONE,
                instance=GPU_INSTANCE_NAME
            ).execute()
            # Wait until running
            while True:
                time.sleep(5)
                status = service.instances().get(
                    project=PROJECT,
                    zone=GPU_INSTANCE_ZONE,
                    instance=GPU_INSTANCE_NAME
                ).execute()
                if status['status'] == 'RUNNING':
                    print(f"✅ GPU VM {GPU_INSTANCE_NAME} is running.")
                    return GPU_INSTANCE_NAME
        else:
            print(f"✅ GPU VM {GPU_INSTANCE_NAME} already running.")
            return GPU_INSTANCE_NAME

    except Exception as e:
        print(f"⚠ Failed to start {GPU_INSTANCE_NAME} in {GPU_INSTANCE_ZONE}: {e}")
    return None

def stop_gpu_vm():
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('compute', 'v1', credentials=credentials)
    print(f"⏹ Stopping GPU VM: {GPU_INSTANCE_NAME} in {GPU_INSTANCE_ZONE}...")
    service.instances().stop(
        project=PROJECT,
        zone=GPU_INSTANCE_ZONE,
        instance=GPU_INSTANCE_NAME
    ).execute()
