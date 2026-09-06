import requests
import os
import sys
import zipfile
import io
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '..', '.env'))

KAGGLE_API = os.getenv('KAGGEL_API')
headers = {'Authorization': f'Bearer {KAGGLE_API}'}
base_url = 'https://www.kaggle.com/api/v1/datasets/download'

datasets_to_download = [
    'asaniczka/data-science-job-postings-and-skills',
    'bismasajjad/global-ai-job-market-and-salary-trends-2025',
    'sumedh1507/college-student-placement',
    'philipdayo/ngess-graduate-employment-dataset',
    'rakesh630/global-student-placement-2025-dataset',
]

output_dir = os.path.join(BASE_DIR, 'kaggle')

for ds in datasets_to_download:
    print(f"Downloading {ds}...")
    try:
        r = requests.get(f'{base_url}/{ds}', headers=headers, stream=True, timeout=60)
        if r.status_code == 200:
            z = zipfile.ZipFile(io.BytesIO(r.content))
            folder_name = ds.split('/')[-1]
            extract_path = os.path.join(output_dir, folder_name)
            os.makedirs(extract_path, exist_ok=True)
            z.extractall(extract_path)
            files = os.listdir(extract_path)
            print(f"  Extracted to {extract_path}: {files}")
        else:
            print(f"  Error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  Exception: {e}")

print("\nDone!")
