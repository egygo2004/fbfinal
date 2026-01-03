from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
import os
import time

ENDPOINT = "https://fra.cloud.appwrite.io/v1"
PROJECT_ID = "finalfb"
API_KEY = "standard_ab59cd2a796312ebf0d2c7ce1b3316c845f05f81afb94eaf4de25b562ee94564da2946616819f3604b36b58c60f5899541648efe9d2b5e3a0a3a9469a19464f36d995a9afbe3bb62b7e5eb33b7e5b78269f0bbda197f862a836eaec6fbafe886226fae4f9caf6a866da99e2327d5f68770c9d203c0868fe34b5f0a36f8229b4b"
DB_ID = "fina"
COLL_PROXY_ID = "proxies"

def fix_proxies():
    client = Client()
    client.set_endpoint(ENDPOINT)
    client.set_project(PROJECT_ID)
    client.set_key(API_KEY)
    databases = Databases(client)
    
    print("[*] Ensuring Proxy Collection...")
    try:
        databases.get_collection(DB_ID, COLL_PROXY_ID)
        print("[+] Collection 'proxies' exists.")
    except:
        print("[-] Collection missing. Creating...")
        databases.create_collection(DB_ID, COLL_PROXY_ID, "Proxies Pool")
        databases.create_string_attribute(DB_ID, COLL_PROXY_ID, "connection_string", 1000, True)
        databases.create_string_attribute(DB_ID, COLL_PROXY_ID, "platform_username", 255, False)
        databases.create_string_attribute(DB_ID, COLL_PROXY_ID, "platform_password", 255, False)
        databases.create_string_attribute(DB_ID, COLL_PROXY_ID, "status", 32, False, "active")
        databases.create_integer_attribute(DB_ID, COLL_PROXY_ID, "usage_count", False, 0, 999999, 0)
        databases.create_datetime_attribute(DB_ID, COLL_PROXY_ID, "last_used", False)
        print("[*] Waiting 10s for attributes...")
        time.sleep(10)
        
    # Check Index
    try:
        databases.create_index(DB_ID, COLL_PROXY_ID, "idx_usage", "key", ["usage_count"], ["ASC"])
        print("[+] Index created.")
    except: pass

    # Add Dummy Proxy
    print("[*] Adding Dummy Proxy...")
    dummy = "us.decodo.com:10001:user-spzpdyn003-sessionduration-1:S~wXakn3z89xeZw0Ps"
    try:
        databases.create_document(
            DB_ID, COLL_PROXY_ID, ID.unique(),
            {
                "connection_string": dummy,
                "status": "active",
                "usage_count": 0
            }
        )
        print("[+] Dummy proxy added.")
    except Exception as e:
        print(f"[-] Proxy add error: {e}")

if __name__ == "__main__":
    fix_proxies()
