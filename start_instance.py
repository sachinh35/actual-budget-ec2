import boto3
import time
import os
import subprocess

INSTANCE_NAME = "Actual Budget EC2"
KEY_FILENAME = "Actual Budget Ec2 Key Pair.pem"
KEY_PATH = os.path.expanduser(f"~/Downloads/{KEY_FILENAME}")
SSH_SESSION_LOC = "/tmp/session1"
KNOWN_HOSTS_PATH = os.path.expanduser("~/.ssh/known_hosts")

ec2 = boto3.Session(profile_name="actual-budget-instance").client("ec2", region_name="us-east-1")

def clean_known_hosts():
    if os.path.exists(KNOWN_HOSTS_PATH):
        with open(KNOWN_HOSTS_PATH, "r") as file:
            lines = file.readlines()
        filtered_lines = [line for line in lines if not line.startswith("ec2-")]
        with open(KNOWN_HOSTS_PATH, "w") as file:
            file.writelines(filtered_lines)
        print("Cleaned known_hosts entries starting with 'ec2-'")


def get_instance_id_by_name(name):
    response = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [name]},
            {"Name": "instance-state-name", "Values": ["stopped", "running"]}
        ]
    )
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            return instance["InstanceId"]
    return None


def start_instance(instance_id):
    print(f"Starting instance {instance_id}...")
    ec2.start_instances(InstanceIds=[instance_id])


def wait_until_running(instance_id):
    print("Waiting for instance to be in 'running' state...")
    waiter = ec2.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id])


def wait_for_status_checks(instance_id):
    print("Waiting for 2/2 status checks to pass...")
    while True:
        statuses = ec2.describe_instance_status(InstanceIds=[instance_id])
        if statuses['InstanceStatuses']:
            status = statuses['InstanceStatuses'][0]
            if (status['InstanceStatus']['Status'] == 'ok' and
                    status['SystemStatus']['Status'] == 'ok'):
                print("✅ Instance passed both status checks.")
                break
        time.sleep(10)


def get_public_ip(instance_id):
    response = ec2.describe_instances(InstanceIds=[instance_id])
    return response["Reservations"][0]["Instances"][0]["PublicIpAddress"]


def ssh_into_instance(ip_address):
    ssh_command = ["ssh", "-i", KEY_PATH, "-f", "-N", "-M", "-S", 
                   SSH_SESSION_LOC, "-L", "5006:localhost:5006", f"ec2-user@{ip_address}",
                   "-o", "StrictHostKeyChecking=no"]
    print(f"Connecting via SSH: {' '.join(ssh_command)}")
    subprocess.run(ssh_command)


def main():
    clean_known_hosts()

    instance_id = get_instance_id_by_name(INSTANCE_NAME)
    if not instance_id:
        print("Instance not found.")
        return

    start_instance(instance_id)
    wait_until_running(instance_id)
    wait_for_status_checks(instance_id)

    ip_address = get_public_ip(instance_id)
    ssh_into_instance(ip_address)


if __name__ == "__main__":
    main()
