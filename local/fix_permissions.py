from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.permission import Permission
from appwrite.role import Role

ENDPOINT = "https://fra.cloud.appwrite.io/v1"
PROJECT_ID = "finalfb"
API_KEY = "standard_ab59cd2a796312ebf0d2c7ce1b3316c845f05f81afb94eaf4de25b562ee94564da2946616819f3604b36b58c60f5899541648efe9d2b5e3a0a3a9469a19464f36d995a9afbe3bb62b7e5eb33b7e5b78269f0bbda197f862a836eaec6fbafe886226fae4f9caf6a866da99e2327d5f68770c9d203c0868fe34b5f0a36f8229b4b"
DB_ID = "fina"

def fix_permissions():
    client = Client()
    client.set_endpoint(ENDPOINT)
    client.set_project(PROJECT_ID)
    client.set_key(API_KEY)
    databases = Databases(client)
    
    collections = ["numbers_queue", "proxies", "settings"]
    
    # Public permissions for dashboard access
    permissions = [
        Permission.read(Role.any()),
        Permission.create(Role.any()),
        Permission.update(Role.any()),
        Permission.delete(Role.any()),
    ]
    
    for coll_id in collections:
        print(f"[*] Updating permissions for {coll_id}...")
        try:
            databases.update_collection(
                database_id=DB_ID,
                collection_id=coll_id,
                name=coll_id.replace("_", " ").title(),
                permissions=permissions,
                document_security=False
            )
            print(f"[+] {coll_id} updated successfully")
        except Exception as e:
            print(f"[-] Error updating {coll_id}: {e}")

if __name__ == "__main__":
    fix_permissions()
