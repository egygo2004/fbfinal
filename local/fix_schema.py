from appwrite.client import Client
from appwrite.services.databases import Databases
import os
import time

ENDPOINT = "https://fra.cloud.appwrite.io/v1"
PROJECT_ID = "finalfb"
API_KEY = "standard_ab59cd2a796312ebf0d2c7ce1b3316c845f05f81afb94eaf4de25b562ee94564da2946616819f3604b36b58c60f5899541648efe9d2b5e3a0a3a9469a19464f36d995a9afbe3bb62b7e5eb33b7e5b78269f0bbda197f862a836eaec6fbafe886226fae4f9caf6a866da99e2327d5f68770c9d203c0868fe34b5f0a36f8229b4b"
DB_ID = "fina"
COLL_QUEUE_ID = "numbers_queue"
DOC_ID = "695961370002e27c1efe"

def fix():
    client = Client()
    client.set_endpoint(ENDPOINT)
    client.set_project(PROJECT_ID)
    client.set_key(API_KEY)
    databases = Databases(client)
    
    print("[*] Checking Attributes...")
    try:
        attrs = databases.list_attributes(DB_ID, COLL_QUEUE_ID)
        existing = [a['key'] for a in attrs['attributes']]
        print(f"    - Existing: {existing}")
        
        if "status" not in existing:
             print("[+] Creating attribute 'status'...")
             databases.create_string_attribute(DB_ID, COLL_QUEUE_ID, "status", 32, False, "pending")
        
        if "created_at" not in existing:
             print("[+] Creating attribute 'created_at'...")
             databases.create_datetime_attribute(DB_ID, COLL_QUEUE_ID, "created_at", False)

        print("[*] Waiting 10s for attribute processing...")
        time.sleep(10)

    except Exception as e: print(f"[-] Attribute check error: {e}")

    print("[*] Creating Indexes...")
    try:
        databases.create_index(DB_ID, COLL_QUEUE_ID, "idx_status", "key", ["status"], ["ASC"])
        print("[+] Index: idx_status created")
    except Exception as e: print(f"[-] idx_status error: {e}")

    try:
        databases.create_index(DB_ID, COLL_QUEUE_ID, "idx_created_at", "key", ["created_at"], ["ASC"])
        print("[+] Index: idx_created_at created")
    except Exception as e: print(f"[-] idx_created_at error: {e}")

    print("[*] Waiting 5s for indexing...")
    time.sleep(5)

    print(f"[*] Updating Document {DOC_ID} status...")
    try:
        databases.update_document(DB_ID, COLL_QUEUE_ID, DOC_ID, {"status": "pending"})
        print("[+] Document updated to 'pending'")
    except Exception as e: print(f"[!] Update error: {e}")

if __name__ == "__main__":
    fix()
