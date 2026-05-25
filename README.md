# ☁️ AWS Cost Optimizer Dashboard

![AWS](https://img.shields.io/badge/AWS-CLF--C02%20%7C%20967%2F1000-FF9900?style=flat&logo=amazonaws&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)
![Region](https://img.shields.io/badge/Region-ap--south--1%20(Mumbai)-232F3E?style=flat&logo=amazonaws)
![Status](https://img.shields.io/badge/Status-Active-1e8e3e?style=flat)
![Last Updated](https://img.shields.io/badge/Last%20Updated-May%202025-blue?style=flat)

> **Built by Varsha** | MCA Graduate | Nashik, Maharashtra  
> AWS Certified Cloud Practitioner — CLF-C02 | Score: **967 / 1000**

---

## 📌 What Problem Does This Solve?

In real AWS environments, **money leaks silently** through:
- EC2 instances that are stopped but still have EBS volumes billing you
- Unattached EBS volumes sitting idle (you pay even when nothing is using them)
- Snapshots piling up for months that nobody reviews
- Empty S3 buckets that were created and forgotten

Most teams don't know these resources exist until they see the AWS bill.

This tool **automatically scans your AWS account**, finds all of these, estimates how much they're costing you every month, and generates a **visual HTML dashboard** — so you can take action immediately.

---

## 🏗️ Architecture
Your AWS Account
│
▼
optimizer.py (Python + boto3)
│
├── EC2 API ──► Scan stopped instances
├── EC2 API ──► Scan unattached EBS volumes
├── EC2 API ──► Scan snapshots older than 30 days
└── S3  API ──► Scan empty buckets
│
▼
Cost Estimation Engine
(EBS: $0.10/GB-month | Snapshots: age-filtered)
│
▼
index.html (Dashboard)
│
▼
Upload to S3 ──► CloudFront ──► Live URL
---

## ✨ Features

| Feature | Description |
|---|---|
| 🖥️ Stopped EC2 Scanner | Finds idle stopped instances with name tags and launch dates |
| 💾 EBS Volume Scanner | Lists unattached volumes with size, type, age and **monthly cost estimate** |
| 📸 Snapshot Scanner | Flags snapshots older than 30 days (configurable) |
| 🪣 S3 Bucket Scanner | Identifies completely empty S3 buckets |
| 💰 Cost Estimator | Calculates estimated monthly savings in USD |
| 📊 HTML Dashboard | Auto-generates a clean, styled visual report |
| 🏷️ Tag-aware | Reads EC2 Name tags for human-readable output |

---

## 🚀 How to Run

### Prerequisites
```bash
pip install boto3
aws configure   # Set your Access Key, Secret Key, Region
```

### Run the scanner
```bash
python optimizer.py
```

### Output
=======================================================
AWS Cost Optimizer — by Varsha (varsha-cloud9)
Region : ap-south-1
[] Scanning for stopped EC2 instances...
Found: 2 stopped instance(s)
[] Scanning for unattached EBS volumes...
Found: 3 unattached volume(s)
[] Scanning for snapshots older than 30 days...
Found: 5 old snapshot(s)
[] Scanning for empty S3 buckets...
Found: 1 empty bucket(s)
✅ Report saved to 'index.html'
📊 Summary:
Stopped Instances  : 2
Unattached Volumes : 3
Old Snapshots      : 5
Empty Buckets      : 1
Est. Monthly Saving: $3.40 USD

---

## 📁 Project Structure
aws-cost-optimizer-nw/
│
├── optimizer.py        # Main scanner script (boto3 + cost estimation)
├── index.html          # Auto-generated HTML dashboard (output)
├── screenshots/        # AWS console screenshots (proof of work)
│   ├── dashboard.png
│   ├── iam-role.png
│   └── s3-hosted.png
├── .gitignore
└── README.md

---

## 🔐 IAM Permissions Required

This tool uses **read-only** permissions only — it never deletes or modifies anything.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeSnapshots",
        "s3:ListAllMyBuckets",
        "s3:ListBucket"
      ],
      "Resource": "*"
    }
  ]
}
```

> ✅ Follows **Least-Privilege Principle** — only the minimum permissions needed.

---

## 💡 What I Learned Building This

- How AWS pricing works for EBS, EC2, and S3 at a detailed level
- Using `boto3` to interact with multiple AWS services from Python
- Importance of **resource tagging** — untagged resources are invisible to teams
- Real companies lose thousands of dollars monthly to orphaned resources
- How to apply the **Least-Privilege IAM principle** in a real script

---

## 🔧 Configuration

You can customize these settings at the top of `optimizer.py`:

```python
SNAPSHOT_AGE_DAYS  = 30           # Flag snapshots older than N days
EBS_COST_PER_GB    = 0.10         # USD/GB-month (change for your region)
REGION             = "ap-south-1" # Your AWS region
```

---

## 👤 About Me

**Varsha** — MCA Graduate | Nashik, Maharashtra, India

- 🏅 AWS Certified Cloud Practitioner (CLF-C02) — Score: **967/1000**
- 💻 Skills: Python, boto3, Linux, AWS (EC2, S3, IAM, VPC, Lambda, CloudFront)
- 🎯 Goal: AWS Solutions Architect
- 🔗 GitHub: [varsha-cloud9](https://github.com/varsha-cloud9)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
