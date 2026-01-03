from appwrite.client import Client
from appwrite.services.databases import Databases
import time

ENDPOINT = "https://fra.cloud.appwrite.io/v1"
PROJECT_ID = "finalfb"
API_KEY = "standard_ab59cd2a796312ebf0d2c7ce1b3316c845f05f81afb94eaf4de25b562ee94564da2946616819f3604b36b58c60f5899541648efe9d2b5e3a0a3a9469a19464f36d995a9afbe3bb62b7e5eb33b7e5b78269f0bbda197f862a836eaec6fbafe886226fae4f9caf6a866da99e2327d5f68770c9d203c0868fe34b5f0a36f8229b4b"
DB_ID = "fina"
COLL_QUEUE_ID = "numbers_queue"

def add_logs_field():
    client = Client()
    client.set_endpoint(ENDPOINT)
    client.set_project(PROJECT_ID)
    client.set_key(API_KEY)
    databases = Databases(client)
    
    print("[*] Adding logs attribute...")
    try:
        databases.create_string_attribute(
            database_id=DB_ID,
            collection_id=COLL_QUEUE_ID,
            key="logs",
            size=10000,  # Allow large logs
            required=False
        )
        print("[+] logs attribute created. Waiting for availability...")
        time.sleep(5)
    except Exception as e:
        if "already exists" in str(e).lower():
            print("[i] logs already exists")
        else:
            print(f"[-] Error: {e}")

if __name__ == "__main__":
    add_logs_field()
