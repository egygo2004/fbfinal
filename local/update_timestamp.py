from appwrite.client import Client
from appwrite.services.databases import Databases
from datetime import datetime
import os

ENDPOINT = "https://fra.cloud.appwrite.io/v1"
PROJECT_ID = "finalfb"
API_KEY = "standard_ab59cd2a796312ebf0d2c7ce1b3316c845f05f81afb94eaf4de25b562ee94564da2946616819f3604b36b58c60f5899541648efe9d2b5e3a0a3a9469a19464f36d995a9afbe3bb62b7e5eb33b7e5b78269f0bbda197f862a836eaec6fbafe886226fae4f9caf6a866da99e2327d5f68770c9d203c0868fe34b5f0a36f8229b4b"
DB_ID = "fina"
COLL_QUEUE_ID = "numbers_queue"
DOC_ID = "695961370002e27c1efe"

def fix_timestamp():
    client = Client()
    client.set_endpoint(ENDPOINT)
    client.set_project(PROJECT_ID)
    client.set_key(API_KEY)
    databases = Databases(client)
    
    print(f"[*] Updating Timestamp for {DOC_ID}...")
    try:
        now_str = datetime.now().isoformat()
        databases.update_document(DB_ID, COLL_QUEUE_ID, DOC_ID, {"created_at": now_str})
        print(f"[+] Document updated with created_at: {now_str}")
    except Exception as e: print(f"[!] Update error: {e}")

if __name__ == "__main__":
    fix_timestamp()
