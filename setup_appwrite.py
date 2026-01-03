"""
Appwrite Schema Setup Script
============================
Run this script to automatically create:
1. Database: FB_OTP_DB
2. Collection: numbers_queue (for processing)
3. Collection: settings (for proxies)
4. Bucket: assets (for screenshots/cookies)

Usage:
    export APPWRITE_ENDPOINT='...'
    export APPWRITE_PROJECT_ID='...'
    export APPWRITE_API_KEY='...'
    python setup_appwrite.py
"""

import os
import sys

try:
    from appwrite.client import Client
    from appwrite.services.databases import Databases
    from appwrite.services.storage import Storage
    from appwrite.id import ID
    from appwrite.enums import IndexType
except ImportError:
    print("Please install appwrite sdk: pip install appwrite")
    sys.exit(1)

# Configuration from Environment or Hardcoded
# ENDPOINT = "https://fra.cloud.appwrite.io/v1"
# PROJECT_ID = "finalfb"
# API_KEY = "standard_..." # (Security: Best to keep in env, but using passed arg for setup)

# For this setup run, we use the provided values or ENV fallbacks
ENDPOINT = os.environ.get("APPWRITE_ENDPOINT", "https://fra.cloud.appwrite.io/v1")
PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID", "finalfb")
API_KEY = os.environ.get("APPWRITE_API_KEY", "standard_ab59cd2a796312ebf0d2c7ce1b3316c845f05f81afb94eaf4de25b562ee94564da2946616819f3604b36b58c60f5899541648efe9d2b5e3a0a3a9469a19464f36d995a9afbe3bb62b7e5eb33b7e5b78269f0bbda197f862a836eaec6fbafe886226fae4f9caf6a866da99e2327d5f68770c9d203c0868fe34b5f0a36f8229b4b")

client = Client()
client.set_endpoint(ENDPOINT)
client.set_project(PROJECT_ID)
client.set_key(API_KEY)

databases = Databases(client)
storage = Storage(client)

DB_NAME = "FB OTP DB"
DB_ID = "fina"  # User provided ID
BUCKET_ID = "finafb" # User provided ID

def setup():
    print(f"[*] Starting setup on {ENDPOINT}...")
    
    # 1. Create Database (if not exists)
    try:
        databases.get(DB_ID)
        print(f"[+] Database {DB_ID} exists.")
    except:
        try:
            databases.create(DB_ID, DB_NAME)
            print(f"[+] Created Database: {DB_ID}")
        except Exception as e: print(f"[!] DB Error: {e}")

    # 2. Collection: numbers_queue
    COLL_QUEUE_ID = "numbers_queue"
    try:
        databases.get_collection(DB_ID, COLL_QUEUE_ID)
        print(f"[+] Collection {COLL_QUEUE_ID} exists.")
    except:
        databases.create_collection(DB_ID, COLL_QUEUE_ID, "Numbers Queue")
        print(f"[+] Created Collection: {COLL_QUEUE_ID}")
        
    # Queue Attributes
    queue_attrs = [
        ("phone", "string", 32, True),
        ("status", "string", 32, True, "pending"),
        ("result_url", "string", 1024, False),
        ("cookie_file_id", "string", 64, False),
        ("screenshot_id", "string", 64, False),
        ("logs", "string", 5000, False),
        ("screenshot_url", "string", 2048, False),
    ]
    for name, type, size, req, *default in queue_attrs:
        try:
            if type == "string": databases.create_string_attribute(DB_ID, COLL_QUEUE_ID, name, size, req, default[0] if default else None)
            print(f"  - Attribute ensured: {name}")
        except: pass
    try: databases.create_datetime_attribute(DB_ID, COLL_QUEUE_ID, "created_at", True)
    except: pass

    # 3. Collection: proxies (New)
    COLL_PROXY_ID = "proxies"
    try:
        databases.get_collection(DB_ID, COLL_PROXY_ID)
        print(f"[+] Collection {COLL_PROXY_ID} exists.")
    except:
        databases.create_collection(DB_ID, COLL_PROXY_ID, "Proxies Pool")
        print(f"[+] Created Collection: {COLL_PROXY_ID}")

    # Proxy Attributes
    proxy_attrs = [
        ("connection_string", 1000, True),  # host:port:user:pass
        ("platform_username", 255, False),
        ("platform_password", 255, False),
        ("status", 32, True, "active"),
    ]
    for name, size, req, *default in proxy_attrs:
        try:
            databases.create_string_attribute(DB_ID, COLL_PROXY_ID, name, size, req, default[0] if default else None)
        except: pass
    
    try: databases.create_integer_attribute(DB_ID, COLL_PROXY_ID, "usage_count", False, 0, 999999, 0)
    except: pass
    try: databases.create_datetime_attribute(DB_ID, COLL_PROXY_ID, "last_used", False)
    except: pass
    print(f"[+] Proxy collection attributes configured.")

    # 4. Collection: settings
    COLL_SETTINGS_ID = "settings"
    try:
        databases.get_collection(DB_ID, COLL_SETTINGS_ID)
        print(f"[+] Collection {COLL_SETTINGS_ID} exists.")
    except:
        databases.create_collection(DB_ID, COLL_SETTINGS_ID, "Settings")
        print(f"[+] Created Collection: {COLL_SETTINGS_ID}")
    
    settings_attrs = [
        ("key", "string", 255, True),
        ("value", "string", 5000, True),
        ("description", "string", 1024, False),
    ]
    for name, type, size, req, *default in settings_attrs:
        try:
             if type == "string": databases.create_string_attribute(DB_ID, COLL_SETTINGS_ID, name, size, req, default[0] if default else None)
        except: pass
    print(f"[+] Settings collection attributes configured.")

    # 4. Storage Bucket
    try:
        storage.get_bucket(BUCKET_ID)
        print(f"[+] Bucket {BUCKET_ID} exists.")
    except:
        storage.create_bucket(BUCKET_ID, "OTP Assets", permission="bucket")
        print(f"[+] Created Bucket: {BUCKET_ID}")

    print("\n[OK] Setup finished successfully!")

if __name__ == "__main__":
    setup()
