from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query

ENDPOINT = "https://fra.cloud.appwrite.io/v1"
PROJECT_ID = "finalfb"
API_KEY = "standard_ab59cd2a796312ebf0d2c7ce1b3316c845f05f81afb94eaf4de25b562ee94564da2946616819f3604b36b58c60f5899541648efe9d2b5e3a0a3a9469a19464f36d995a9afbe3bb62b7e5eb33b7e5b78269f0bbda197f862a836eaec6fbafe886226fae4f9caf6a866da99e2327d5f68770c9d203c0868fe34b5f0a36f8229b4b"
DB_ID = "fina"
QUEUE_COLL_ID = "numbers_queue"

client = Client()
client.set_endpoint(ENDPOINT)
client.set_project(PROJECT_ID)
client.set_key(API_KEY)
databases = Databases(client)

print("[*] Finding stuck PROCESSING tasks...")
result = databases.list_documents(DB_ID, QUEUE_COLL_ID, [
    Query.equal("status", "processing")
])

print(f"[*] Found {result['total']} stuck tasks")
for doc in result['documents']:
    print(f"   Resetting: {doc['phone']} ({doc['$id']})")
    databases.update_document(DB_ID, QUEUE_COLL_ID, doc['$id'], {
        "status": "failed",
        "error_reason": "STUCK_RESET"
    })
    print(f"   [+] Reset to failed")

print("\n[OK] Done!")
