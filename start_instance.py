import boto3

ec2 = boto3.Session(profile_name="actual-budget-instance").client("ec2", region_name="us-east-1")

response = ec2.describe_instances()

print(response['Reservations'][0])