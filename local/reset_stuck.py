from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query

ENDPOINT = "https://fra.cloud.appwrite.io/v1"
PROJECT_ID = "finalfb"
API_KEY = "standard_ab59cd2a796312ebf0d2c7ce1b3316c845f05f81afb94eaf4de25b562ee94564da2946616819f3604b36b58c60f5899541648efe9d2b5e3a0a3a9469a19464f36d995a9afbe3bb62b7e5eb33b7e5b78269f0bbda197f862a836eaec6fbafe886226fae4f9caf6a866da99e2327d5f68770c9d203c0868fe34b5f0a36f8229b4b"
DB_ID = "fina"
COLL_QUEUE_ID = "numbers_queue"

def reset_stuck():
    client = Client()
    client.set_endpoint(ENDPOINT)
    client.set_project(PROJECT_ID)
    client.set_key(API_KEY)
    databases = Databases(client)
    
    print("[*] Finding stuck PROCESSING tasks...")
    try:
        result = databases.list_documents(
            DB_ID, 
            COLL_QUEUE_ID, 
            [Query.equal("status", "processing"), Query.limit(50)]
        )
        print(f"[+] Found {result['total']} stuck tasks.")
        
        for doc in result['documents']:
            print(f"    - Resetting {doc.get('phone')} to 'failed'...")
            databases.update_document(
                DB_ID, COLL_QUEUE_ID, doc['$id'],
                {"status": "failed"}
            )
            print(f"    [+] Done.")
                
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    reset_stuck()
