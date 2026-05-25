"""
=============================================================
  AWS Cost Optimizer Dashboard
  Author  : Varsha (varsha-cloud9)
  GitHub  : https://github.com/varsha-cloud9/aws-cost-optimizer-nw
  Cert    : AWS Certified Cloud Practitioner | CLF-C02 | Score: 967/1000
  Purpose : Scan AWS account for idle/unused resources and
            estimate potential monthly savings.
=============================================================
"""

import boto3
import json
from datetime import datetime, timezone

# ── CONFIG ────────────────────────────────────────────────
SNAPSHOT_AGE_DAYS   = 30          # Flag snapshots older than this
EBS_COST_PER_GB     = 0.10        # USD per GB-month (gp2 pricing)
EC2_COST_PER_HOUR   = 0.0116      # USD/hr for t2.micro (stopped = still paying for EBS)
REPORT_FILE         = "index.html"
REGION              = "ap-south-1"   # Mumbai — Varsha's primary region
# ──────────────────────────────────────────────────────────


def days_old(dt):
    """Return how many days old a datetime object is."""
    now = datetime.now(timezone.utc)
    return (now - dt).days


def get_idle_resources():
    """Scan AWS account and return dict of idle/unused resources with cost estimates."""

    ec2 = boto3.client("ec2", region_name=REGION)
    s3  = boto3.client("s3",  region_name=REGION)

    report = {
        "scan_time"           : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "region"              : REGION,
        "stopped_instances"   : [],
        "unattached_volumes"  : [],
        "old_snapshots"       : [],
        "empty_buckets"       : [],
        "estimated_savings"   : 0.0,
    }

    # ── 1. Stopped EC2 Instances ──────────────────────────
    print("[*] Scanning for stopped EC2 instances...")
    resp = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
    )
    for reservation in resp["Reservations"]:
        for inst in reservation["Instances"]:
            name = next(
                (t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"),
                "Unnamed"
            )
            report["stopped_instances"].append({
                "id"         : inst["InstanceId"],
                "name"       : name,
                "type"       : inst["InstanceType"],
                "launched"   : str(inst["LaunchTime"].date()),
                "days_stopped": days_old(inst["LaunchTime"]),
            })
    print(f"    Found: {len(report['stopped_instances'])} stopped instance(s)")

    # ── 2. Unattached EBS Volumes ─────────────────────────
    print("[*] Scanning for unattached EBS volumes...")
    vols = ec2.describe_volumes(
        Filters=[{"Name": "status", "Values": ["available"]}]
    )
    for vol in vols["Volumes"]:
        size_gb      = vol["Size"]
        monthly_cost = round(size_gb * EBS_COST_PER_GB, 2)
        report["estimated_savings"] += monthly_cost
        report["unattached_volumes"].append({
            "id"          : vol["VolumeId"],
            "size_gb"     : size_gb,
            "volume_type" : vol["VolumeType"],
            "created_days": days_old(vol["CreateTime"]),
            "monthly_cost": monthly_cost,
        })
    print(f"    Found: {len(report['unattached_volumes'])} unattached volume(s)")

    # ── 3. Old Snapshots (older than SNAPSHOT_AGE_DAYS) ───
    print(f"[*] Scanning for snapshots older than {SNAPSHOT_AGE_DAYS} days...")
    snaps = ec2.describe_snapshots(OwnerIds=["self"])
    for snap in snaps["Snapshots"]:
        age = days_old(snap["StartTime"])
        if age >= SNAPSHOT_AGE_DAYS:
            report["old_snapshots"].append({
                "id"         : snap["SnapshotId"],
                "size_gb"    : snap["VolumeSize"],
                "age_days"   : age,
                "description": snap.get("Description", "No description")[:60],
            })
    print(f"    Found: {len(report['old_snapshots'])} old snapshot(s)")

    # ── 4. Empty S3 Buckets ───────────────────────────────
    print("[*] Scanning for empty S3 buckets...")
    buckets = s3.list_buckets()
    for bucket in buckets["Buckets"]:
        name = bucket["Name"]
        try:
            objects = s3.list_objects_v2(Bucket=name, MaxKeys=1)
            if "Contents" not in objects:
                report["empty_buckets"].append({"name": name})
        except Exception:
            continue
    print(f"    Found: {len(report['empty_buckets'])} empty bucket(s)")

    report["estimated_savings"] = round(report["estimated_savings"], 2)
    return report


def generate_html_report(data):
    """Generate a styled HTML dashboard from scan results."""

    def rows(items, keys, labels, empty_msg):
        if not items:
            return f'<tr><td colspan="{len(keys)}" class="clean">✅ {empty_msg}</td></tr>'
        return "".join(
            "<tr>" + "".join(f"<td>{item.get(k,'-')}</td>" for k, _ in zip(keys, labels)) + "</tr>"
            for item in items
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AWS Cost Optimizer | varsha-cloud9</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Arial, sans-serif; background: #f0f2f5; color: #232f3e; }}
    header {{ background: #232f3e; color: white; padding: 24px 40px; }}
    header h1 {{ font-size: 24px; }}
    header p  {{ font-size: 13px; color: #aab7c4; margin-top: 4px; }}
    .badges {{ margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap; }}
    .badge {{ background: #ec922c; color: white; padding: 3px 12px;
              border-radius: 20px; font-size: 12px; font-weight: bold; }}
    .badge.green  {{ background: #1e8e3e; }}
    .badge.blue   {{ background: #1a73e8; }}
    main {{ padding: 30px 40px; }}
    .summary {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 30px; }}
    .stat {{ background: white; border-radius: 10px; padding: 20px 28px;
             flex: 1; min-width: 160px; box-shadow: 0 2px 8px rgba(0,0,0,.08);
             border-top: 4px solid #ec922c; }}
    .stat.green {{ border-top-color: #1e8e3e; }}
    .stat.blue  {{ border-top-color: #1a73e8; }}
    .stat .num  {{ font-size: 32px; font-weight: bold; color: #ec922c; }}
    .stat.green .num {{ color: #1e8e3e; }}
    .stat.blue  .num {{ color: #1a73e8; }}
    .stat .lbl  {{ font-size: 13px; color: #666; margin-top: 4px; }}
    .card {{ background: white; border-radius: 10px; margin-bottom: 24px;
             box-shadow: 0 2px 8px rgba(0,0,0,.08); overflow: hidden; }}
    .card-header {{ background: #232f3e; color: white; padding: 14px 20px;
                    font-size: 15px; font-weight: bold; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ background: #f8f9fa; padding: 10px 16px; text-align: left;
          font-size: 12px; color: #666; border-bottom: 1px solid #e0e0e0; }}
    td {{ padding: 10px 16px; font-size: 13px; border-bottom: 1px solid #f0f0f0; }}
    tr:last-child td {{ border-bottom: none; }}
    td.clean {{ color: #1e8e3e; font-weight: bold; }}
    .warn {{ color: #ec922c; font-weight: bold; }}
    footer {{ text-align: center; padding: 20px; font-size: 12px; color: #999; }}
  </style>
</head>
<body>
<header>
  <h1>☁️ AWS Cost Optimizer Dashboard</h1>
  <p>Region: {data['region']} &nbsp;|&nbsp; Scan Time: {data['scan_time']} IST</p>
  <div class="badges">
    <span class="badge">varsha-cloud9</span>
    <span class="badge green">AWS CLF-C02 ✓ 967/1000</span>
    <span class="badge blue">MCA Graduate</span>
  </div>
</header>
<main>

  <div class="summary">
    <div class="stat">
      <div class="num">{len(data['stopped_instances'])}</div>
      <div class="lbl">Stopped EC2 Instances</div>
    </div>
    <div class="stat">
      <div class="num">{len(data['unattached_volumes'])}</div>
      <div class="lbl">Unattached EBS Volumes</div>
    </div>
    <div class="stat">
      <div class="num">{len(data['old_snapshots'])}</div>
      <div class="lbl">Old Snapshots (30+ days)</div>
    </div>
    <div class="stat">
      <div class="num">{len(data['empty_buckets'])}</div>
      <div class="lbl">Empty S3 Buckets</div>
    </div>
    <div class="stat green">
      <div class="num">${data['estimated_savings']}</div>
      <div class="lbl">Est. Monthly Savings (USD)</div>
    </div>
  </div>

  <div class="card">
    <div class="card-header">🖥️ Stopped EC2 Instances ({len(data['stopped_instances'])})</div>
    <table>
      <tr><th>Instance ID</th><th>Name</th><th>Type</th><th>Launched</th><th>Days Idle</th></tr>
      {rows(data['stopped_instances'],
            ['id','name','type','launched','days_stopped'],
            ['Instance ID','Name','Type','Launched','Days Idle'],
            'No stopped instances found — all instances are running!')}
    </table>
  </div>

  <div class="card">
    <div class="card-header">💾 Unattached EBS Volumes ({len(data['unattached_volumes'])})</div>
    <table>
      <tr><th>Volume ID</th><th>Size (GB)</th><th>Type</th><th>Age (Days)</th><th>Monthly Cost (USD)</th></tr>
      {rows(data['unattached_volumes'],
            ['id','size_gb','volume_type','created_days','monthly_cost'],
            ['Volume ID','Size','Type','Age','Cost'],
            'No unattached volumes found — storage is clean!')}
    </table>
  </div>

  <div class="card">
    <div class="card-header">📸 Old Snapshots — 30+ Days ({len(data['old_snapshots'])})</div>
    <table>
      <tr><th>Snapshot ID</th><th>Size (GB)</th><th>Age (Days)</th><th>Description</th></tr>
      {rows(data['old_snapshots'],
            ['id','size_gb','age_days','description'],
            ['Snapshot ID','Size','Age','Description'],
            'No old snapshots found — backups are well managed!')}
    </table>
  </div>

  <div class="card">
    <div class="card-header">🪣 Empty S3 Buckets ({len(data['empty_buckets'])})</div>
    <table>
      <tr><th>Bucket Name</th></tr>
      {rows(data['empty_buckets'],
            ['name'],['Bucket Name'],
            'No empty buckets found — storage is optimized!')}
    </table>
  </div>

</main>
<footer>
  Built by <strong>Varsha</strong> | AWS CLF-C02 (967/1000) | MCA Graduate | Nashik, Maharashtra
  &nbsp;·&nbsp; <a href="https://github.com/varsha-cloud9/aws-cost-optimizer-nw">GitHub Repo</a>
</footer>
</body>
</html>"""

    with open(REPORT_FILE, "w") as f:
        f.write(html)
    print(f"\n✅ Report saved to '{REPORT_FILE}'")


if __name__ == "__main__":
    print("=" * 55)
    print("  AWS Cost Optimizer — by Varsha (varsha-cloud9)")
    print(f"  Region : {REGION}")
    print("=" * 55)
    data = get_idle_resources()
    generate_html_report(data)
    print(f"\n📊 Summary:")
    print(f"   Stopped Instances  : {len(data['stopped_instances'])}")
    print(f"   Unattached Volumes : {len(data['unattached_volumes'])}")
    print(f"   Old Snapshots      : {len(data['old_snapshots'])}")
    print(f"   Empty Buckets      : {len(data['empty_buckets'])}")
    print(f"   Est. Monthly Saving: ${data['estimated_savings']} USD")
    print("=" * 55)
