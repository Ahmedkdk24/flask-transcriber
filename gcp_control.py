from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from config import PROJECT, ZONES_INSTANCES
import time

def start_gpu_vm():
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('compute', 'v1', credentials=credentials)

    for instance_name, zone in ZONES_INSTANCES:
        try:
            status = service.instances().get(project=PROJECT, zone=zone, instance=instance_name).execute()
            if status['status'] != 'RUNNING':
                print(f"▶ Starting GPU VM: {instance_name} in {zone}...")
                service.instances().start(project=PROJECT, zone=zone, instance=instance_name).execute()
                # Wait until running
                while True:
                    time.sleep(5)
                    status = service.instances().get(project=PROJECT, zone=zone, instance=instance_name).execute()
                    if status['status'] == 'RUNNING':
                        print(f"✅ GPU VM {instance_name} is running.")
                        return instance_name
            else:
                print(f"✅ GPU VM {instance_name} already running.")
                return instance_name
        except Exception as e:
            print(f"⚠ Failed to start {instance_name} in {zone}: {e}")
    return None

def stop_gpu_vm(instance_name, zone):
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('compute', 'v1', credentials=credentials)
    print(f"⏹ Stopping GPU VM: {instance_name} in {zone}...")
    service.instances().stop(project=PROJECT, zone=zone, instance=instance_name).execute()
