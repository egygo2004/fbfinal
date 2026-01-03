from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
import os

# Config (matching setup_appwrite.py)
ENDPOINT = "https://fra.cloud.appwrite.io/v1"
PROJECT_ID = "finalfb"
API_KEY = "standard_ab59cd2a796312ebf0d2c7ce1b3316c845f05f81afb94eaf4de25b562ee94564da2946616819f3604b36b58c60f5899541648efe9d2b5e3a0a3a9469a19464f36d995a9afbe3bb62b7e5eb33b7e5b78269f0bbda197f862a836eaec6fbafe886226fae4f9caf6a866da99e2327d5f68770c9d203c0868fe34b5f0a36f8229b4b"
DB_ID = "fina"
COLL_QUEUE_ID = "numbers_queue"

def add_test_number():
    client = Client()
    client.set_endpoint(ENDPOINT)
    client.set_project(PROJECT_ID)
    client.set_key(API_KEY)
    
    databases = Databases(client)
    
    try:
        print(f"[*] Adding test number +201000000000 to {DB_ID}/{COLL_QUEUE_ID}...")
        try:
            databases.get_collection(DB_ID, COLL_QUEUE_ID)
        except:
             print("[!] Collection missing, creating...")
             databases.create_collection(DB_ID, COLL_QUEUE_ID, "Numbers Queue")
             databases.create_string_attribute(DB_ID, COLL_QUEUE_ID, "phone", 32, True)
             databases.create_string_attribute(DB_ID, COLL_QUEUE_ID, "status", 32, False, "pending")
             databases.create_string_attribute(DB_ID, COLL_QUEUE_ID, "result_url", 1024, False)
             databases.create_string_attribute(DB_ID, COLL_QUEUE_ID, "cookie_file_id", 64, False)
             databases.create_string_attribute(DB_ID, COLL_QUEUE_ID, "screenshot_id", 64, False)
             databases.create_string_attribute(DB_ID, COLL_QUEUE_ID, "logs", 5000, False)
             databases.create_string_attribute(DB_ID, COLL_QUEUE_ID, "screenshot_url", 2048, False)
             databases.create_datetime_attribute(DB_ID, COLL_QUEUE_ID, "created_at", True)
             # Wait for attributes
             import time
             time.sleep(5)

        result = databases.create_document(
            database_id=DB_ID,
            collection_id=COLL_QUEUE_ID,
            document_id=ID.unique(),
            data={
                "phone": "+201000000000"
            }
        )
        print(f"[+] Successfully added document: {result['$id']}")
        print("[*] Worker should pick this up momentarily.")
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    add_test_number()
