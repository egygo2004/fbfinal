from appwrite.client import Client
from appwrite.services.databases import Databases
import os

ENDPOINT = "https://fra.cloud.appwrite.io/v1"
PROJECT_ID = "finalfb"
API_KEY = "standard_ab59cd2a796312ebf0d2c7ce1b3316c845f05f81afb94eaf4de25b562ee94564da2946616819f3604b36b58c60f5899541648efe9d2b5e3a0a3a9469a19464f36d995a9afbe3bb62b7e5eb33b7e5b78269f0bbda197f862a836eaec6fbafe886226fae4f9caf6a866da99e2327d5f68770c9d203c0868fe34b5f0a36f8229b4b"
DB_ID = "fina"
COLL_QUEUE_ID = "numbers_queue"
DOC_ID = "695961370002e27c1efe"

def check():
    client = Client()
    client.set_endpoint(ENDPOINT)
    client.set_project(PROJECT_ID)
    client.set_key(API_KEY)
    
    databases = Databases(client)
    
    # Check Document
    try:
        print(f"[*] Fetching document {DOC_ID}...")
        doc = databases.get_document(DB_ID, COLL_QUEUE_ID, DOC_ID)
        print(f"    - Phone: {doc.get('phone')}")
        print(f"    - Status: '{doc.get('status')}'")
        print(f"    - Created At: {doc.get('created_at')}")
    except Exception as e:
        print(f"[!] Document Error: {e}")

    # Check Indexes
    try:
        print(f"[*] Listing Indexes for {COLL_QUEUE_ID}...")
        indexes = databases.list_indexes(DB_ID, COLL_QUEUE_ID)
        if indexes['total'] == 0:
            print("    [!] NO INDEXES FOUND! Queries will fail.")
        else:
            for idx in indexes['indexes']:
                print(f"    - Index: {idx['key']} (Status: {idx['status']}, Attrs: {idx['attributes']})")
    except Exception as e:
        print(f"[!] Index check error: {e}")

if __name__ == "__main__":
    check()
