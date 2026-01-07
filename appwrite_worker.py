"""
Appwrite Client for Python Worker
=================================
Handles polling for numbers and updating results.
"""

import os
import json
import time
from datetime import datetime
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.query import Query
from appwrite.input_file import InputFile

class AppwriteWorkerClient:
    def __init__(self, endpoint, project_id, api_key):
        self.client = Client()
        self.client.set_endpoint(endpoint)
        self.client.set_project(project_id)
        self.client.set_key(api_key)
        
        self.databases = Databases(self.client)
        self.storage = Storage(self.client)
        
        self.db_id = "fina"
        self.queue_id = "numbers_queue"
        self.proxy_id = "proxies" # New
        self.bucket_id = "finafb"

    def get_pending_number(self):
        """Fetch one random pending number from the top 30 queue to avoid collisions"""
        try:
            import random
            result = self.databases.list_documents(
                self.db_id,
                self.queue_id,
                [
                    Query.equal("status", "pending"),
                    Query.order_asc("created_at"),
                    Query.limit(30) # Fetch batch to allow random selection
                ]
            )
            if result['total'] > 0:
                # Pick a random document to reduce race conditions between 10 workers
                return random.choice(result['documents'])
        except Exception as e:
            print(f"[Appwrite] Error fetching pending: {e}")
        return None

    def get_best_proxy(self):
        """Fetch the best active proxy (least used)"""
        try:
            result = self.databases.list_documents(
                self.db_id,
                self.proxy_id,
                [
                    Query.equal("status", "active"),
                    Query.order_asc("usage_count"),
                    Query.limit(1)
                ]
            )
            if result['total'] > 0:
                p = result['documents'][0]
                # Parse host:port:user:pass
                parts = p['connection_string'].split(':')
                if len(parts) == 4:
                    return {
                        "id": p['$id'],
                        "host": parts[0],
                        "port": int(parts[1]),
                        "username": parts[2],
                        "password": parts[3]
                    }
        except Exception as e:
            print(f"[Appwrite] Error fetching proxy: {e}")
        return None

    def report_proxy_usage(self, proxy_id, success=True):
        """Increment usage count (proxy stays active regardless of success/failure)"""
        try:
            doc = self.databases.get_document(self.db_id, self.proxy_id, proxy_id)
            data = {
                "last_used": datetime.now().isoformat(),
                "usage_count": (doc.get("usage_count", 0) or 0) + 1
            }
            # Note: We no longer set status to "failed" - proxy stays active
            # This prevents one failure from blocking all remaining numbers
            self.databases.update_document(self.db_id, self.proxy_id, proxy_id, data)
        except Exception as e:
            print(f"[Appwrite] Error reporting proxy: {e}")

    def append_log(self, doc_id, message):
        """Append a log entry to track progress"""
        try:
            doc = self.databases.get_document(self.db_id, self.queue_id, doc_id)
            existing_logs = doc.get("logs", "") or ""
            timestamp = datetime.now().strftime("%H:%M:%S")
            new_log = f"[{timestamp}] {message}\n"
            updated_logs = (existing_logs + new_log)[-8000:]  # Keep last 8000 chars
            self.databases.update_document(self.db_id, self.queue_id, doc_id, {"logs": updated_logs})
        except Exception as e:
            print(f"[Appwrite] Log append error: {e}")

    def update_status(self, doc_id, status, result_url=None, error_reason=None, screenshot_path=None, cookies_json=None, logs=None):
        """Update the status and upload assets"""
        data = {"status": status}
        if result_url: data["result_url"] = result_url
        if error_reason: data["error_reason"] = error_reason[:500]
        if logs: data["logs"] = logs[-8000:]
        
        # Try to upload Screenshot (separate try so failure doesn't block status update)
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                print(f"[Appwrite] Uploading screenshot: {screenshot_path}")
                # Short unique ID: s_{doc_id} (2+20=22 chars) - safe
                file_id = f"s_{doc_id}" 
                file_result = self.storage.create_file(
                    self.bucket_id,
                    file_id,
                    InputFile.from_path(screenshot_path)
                )
                data["screenshot_id"] = file_result['$id']
                print(f"[Appwrite] Screenshot uploaded: {file_result['$id']}")
            except Exception as e:
                print(f"[Appwrite] Screenshot upload failed: {e}")

        # Try to upload Cookies (separate try so failure doesn't block status update)
        if cookies_json:
            # Save inline JSON for dashboard display (truncate to 50000 chars)
            try:
                cookies_str = json.dumps(cookies_json)
                data["cookies_json"] = cookies_str[:50000]
            except: pass
            
            # Also upload as file for download
            try:
                print(f"[Appwrite] Uploading cookies...")
                cookie_path = f"tmp_cookies_{doc_id}.json"
                with open(cookie_path, 'w') as f:
                    json.dump(cookies_json, f)
                
                # Short unique ID: c_{doc_id} (2+20=22 chars) - safe
                file_id = f"c_{doc_id}"
                file_result = self.storage.create_file(
                    self.bucket_id,
                    file_id,
                    InputFile.from_path(cookie_path)
                )
                data["cookie_file_id"] = file_result['$id']
                print(f"[Appwrite] Cookies uploaded: {file_result['$id']}")
                os.remove(cookie_path)
            except Exception as e:
                print(f"[Appwrite] Cookie upload failed: {e}")

        # ALWAYS try to update the status (this is critical)
        try:
            print(f"[Appwrite] Updating status to: {status}")
            self.databases.update_document(self.db_id, self.queue_id, doc_id, data)
            print(f"[Appwrite] ✅ Updated {doc_id} to {status}")
        except Exception as e:
            print(f"[Appwrite] ❌ Error updating status: {e}")

    def get_proxy_config(self):
        """Fetch proxy config from settings collection"""
        try:
            result = self.databases.list_documents(
                self.db_id,
                self.settings_id,
                [Query.equal("key", "proxy_config")]
            )
            if result['total'] > 0:
                return json.loads(result['documents'][0]['value'])
        except Exception as e:
            print(f"[Appwrite] Error fetching proxy: {e}")
        return None
