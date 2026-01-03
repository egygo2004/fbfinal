import os
import sys
import time

print("[*] Starting Debug Script on Heroku...")
try:
    from appwrite_worker import AppwriteWorkerClient
    print("[+] AppwriteWorkerClient execution module imported.")
except ImportError as e:
    print(f"[-] ImportError: {e}")
    sys.exit(1)

endpoint = os.environ.get('APPWRITE_ENDPOINT')
project = os.environ.get('APPWRITE_PROJECT_ID')
key = os.environ.get('APPWRITE_API_KEY')

print(f"[*] Config: Endpoint={endpoint}, Project={project}, Key={'*' * 5 if key else 'None'}")

if not key:
    print("[-] Missing Key")
    sys.exit(1)

try:
    w = AppwriteWorkerClient(endpoint, project, key)
    print("[+] Client initialized.")
    
    print("[*] Fetching pending number...")
    t = w.get_pending_number()
    if t:
        print(f"[+] TASK FOUND: {t}")
    else:
        print("[-] No task found (result is None).")
        
except Exception as e:
    print(f"[!] execution Error: {e}")
