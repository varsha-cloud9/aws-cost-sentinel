import boto3

def get_idle_resources():
    ec2 = boto3.client('ec2')
    s3 = boto3.client('s3')
    
    report_data = {
        "stopped_instances": [],
        "unattached_volumes": [],
        "old_snapshots": [],
        "empty_buckets": []
    }
    
    # 1. Check for Stopped EC2 Instances
    instances = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])
    for reservation in instances['Reservations']:
        for inst in reservation['Instances']:
            report_data["stopped_instances"].append(inst['InstanceId'])
            
    # 2. Check for Unattached EBS Volumes
    volumes = ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
    for vol in volumes['Volumes']:
        report_data["unattached_volumes"].append(vol['VolumeId'])
        
    # 3. Check for Old Snapshots (Created by you, older than 30 days could be checked, listing all here for demo)
    snapshots = ec2.describe_snapshots(OwnerIds=['self'])
    for snap in snapshots['Snapshots']:
        report_data["old_snapshots"].append(snap['SnapshotId'])
        
    # 4. Check for Empty S3 Buckets
    buckets = s3.list_buckets()
    for bucket in buckets['Buckets']:
        name = bucket['Name']
        try:
            objects = s3.list_objects_v2(Bucket=name, MaxKeys=1)
            if 'Contents' not in objects:
                report_data["empty_buckets"].append(name)
        except Exception:
            continue # Skip buckets you don't have access to read
            
    return report_data

def generate_html_report(data):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AWS Cost Optimizer Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f4f6f9; }}
            .card {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ color: #232f3e; }}
            h3 {{ color: #ec922c; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ background: #fdf3e6; margin: 5px 0; padding: 10px; border-left: 5px solid #ec922c; }}
            .clean {{ background: #e6f4ea; border-left: 5px solid #34a853; }}
        </style>
    </head>
    <body>
        <h1>AWS Cost Optimization Report</h1>
        <p>Potential Monthly Savings Target: <strong>35%+</strong> by cleaning orphaned resources.</p>
        
        <div class="card">
            <h3>Stopped EC2 Instances ({len(data['stopped_instances'])})</h3>
            <ul>{"".join([f"<li>{x}</li>" for x in data['stopped_instances']]) if data['stopped_instances'] else "<li class='clean'>No idle stopped instances found!</li>"}</ul>
        </div>
        
        <div class="card">
            <h3>Unattached EBS Volumes ({len(data['unattached_volumes'])})</h3>
            <ul>{"".join([f"<li>{x}</li>" for x in data['unattached_volumes']]) if data['unattached_volumes'] else "<li class='clean'>No orphaned volumes found!</li>"}</ul>
        </div>
        
        <div class="card">
            <h3>AWS Snapshots ({len(data['old_snapshots'])})</h3>
            <ul>{"".join([f"<li>{x}</li>" for x in data['old_snapshots']]) if data['old_snapshots'] else "<li class='clean'>No independent snapshots found!</li>"}</ul>
        </div>
        
        <div class="card">
            <h3>Empty S3 Buckets ({len(data['empty_buckets'])})</h3>
            <ul>{"".join([f"<li>{x}</li>" for x in data['empty_buckets']]) if data['empty_buckets'] else "<li class='clean'>No empty buckets found!</li>"}</ul>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w") as f:
        f.write(html_content)
    print("Report generated successfully as index.html")

if __name__ == "__main__":
    resource_data = get_idle_resources()
    generate_html_report(resource_data)