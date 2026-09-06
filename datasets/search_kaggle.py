import requests
import os
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '..', '.env'))

KAGGLE_API = os.getenv('KAGGEL_API')
headers = {'Authorization': f'Bearer {KAGGLE_API}'}

# Search for skill gap datasets
r = requests.get('https://www.kaggle.com/api/v1/datasets/list?search=skill+gap+job&page=1&pageSize=20', headers=headers)
data = r.json()
print("=== Kaggle: skill gap job ===")
for d in data[:10]:
    ref = d.get('ref', 'N/A')
    title = d.get('title', 'N/A')
    size = d.get('totalBytes', 0)
    print(f"  {ref} - {title} ({size/1024:.1f} KB)")

# Search for job market skills
r2 = requests.get('https://www.kaggle.com/api/v1/datasets/list?search=job+market+skills&page=1&pageSize=20', headers=headers)
data2 = r2.json()
print("\n=== Kaggle: job market skills ===")
for d in data2[:10]:
    ref = d.get('ref', 'N/A')
    title = d.get('title', 'N/A')
    size = d.get('totalBytes', 0)
    print(f"  {ref} - {title} ({size/1024:.1f} KB)")

# Search for academic employment
r3 = requests.get('https://www.kaggle.com/api/v1/datasets/list?search=academic+employment+skills&page=1&pageSize=20', headers=headers)
data3 = r3.json()
print("\n=== Kaggle: academic employment skills ===")
for d in data3[:10]:
    ref = d.get('ref', 'N/A')
    title = d.get('title', 'N/A')
    size = d.get('totalBytes', 0)
    print(f"  {ref} - {title} ({size/1024:.1f} KB)")
