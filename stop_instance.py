import boto3
import time
import subprocess

INSTANCE_NAME = "Actual Budget EC2"
SSH_SESSION_LOC = "/tmp/session1"

ec2 = boto3.Session(profile_name="actual-budget-instance").client("ec2", region_name="us-east-1")

def close_ssh_connection(ip_address):
    ssh_command = ["ssh", "-S", SSH_SESSION_LOC, "-O", "exit", f"ec2-user@{ip_address}"]
    print(f"Disconnecting SSH session: {' '.join(ssh_command)}")
    subprocess.run(ssh_command)

def get_public_ip(instance_id):
    response = ec2.describe_instances(InstanceIds=[instance_id])
    return response["Reservations"][0]["Instances"][0]["PublicIpAddress"]


def get_instance_id_by_name(name):
    response = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [name]},
            {"Name": "instance-state-name", "Values": ["running", "stopping", "stopped"]}
        ]
    )
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            return instance["InstanceId"]
    return None


def stop_instance(instance_id):
    print(f"Stopping instance {instance_id}...")
    ec2.stop_instances(InstanceIds=[instance_id])


def wait_until_stopped(instance_id):
    print("Polling until instance is fully stopped...")
    while True:
        response = ec2.describe_instance_status(InstanceIds=[instance_id], IncludeAllInstances=True)
        if response["InstanceStatuses"]:
            state = response["InstanceStatuses"][0]["InstanceState"]["Name"]
            print(f"Current state: {state}")
            if state == "stopped":
                print("✅ Instance is now stopped.")
                break
        else:
            # Once fully stopped, describe_instance_status may return nothing
            print("No instance status returned (likely fully stopped).")
            break
        time.sleep(10)


def main():
    instance_id = get_instance_id_by_name(INSTANCE_NAME)
    if not instance_id:
        print("Instance not found.")
        return
    
    ip_address = get_public_ip(instance_id)
    close_ssh_connection(ip_address)
    stop_instance(instance_id)
    wait_until_stopped(instance_id)


if __name__ == "__main__":
    main()
