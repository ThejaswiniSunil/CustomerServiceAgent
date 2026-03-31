import os
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from dotenv import load_dotenv

load_dotenv()
db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))

complaints = [
    {"product_name": "Sony WH-1000XM5", "issue_type": "defect",
     "urgency_level": "high", "customer_emotion": "frustrated",
     "resolution": "replacement", "days_since_purchase": 12, "priority": "high"},
    {"product_name": "Sony WH-1000XM5", "issue_type": "defect",
     "urgency_level": "high", "customer_emotion": "angry",
     "resolution": "refund", "days_since_purchase": 5, "priority": "urgent"},
    {"product_name": "Nike Air Max", "issue_type": "damaged",
     "urgency_level": "medium", "customer_emotion": "disappointed",
     "resolution": "replacement", "days_since_purchase": 20, "priority": "medium"},
    {"product_name": "Sony WH-1000XM5", "issue_type": "defect",
     "urgency_level": "high", "customer_emotion": "angry",
     "resolution": "refund", "days_since_purchase": 8, "priority": "high"},
    {"product_name": "Samsung TV", "issue_type": "not_as_described",
     "urgency_level": "low", "customer_emotion": "neutral",
     "resolution": "partial_refund", "days_since_purchase": 45, "priority": "low"},
    {"product_name": "Nike Air Max", "issue_type": "damaged",
     "urgency_level": "medium", "customer_emotion": "frustrated",
     "resolution": "replacement", "days_since_purchase": 15, "priority": "medium"},
]

for i, c in enumerate(complaints):
    c["is_resolved"] = True
    c["complaint_summary"] = f"Test complaint {i+1}"
    c["created_at"] = datetime.now(timezone.utc) - timedelta(hours=i)
    db.collection("complaints").add(c)
    print(f"Seeded complaint {i+1}: {c['product_name']} - {c['issue_type']}")

print("Done. Now run improve() to test the learning agent.")