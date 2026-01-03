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
        """Fetch one pending number from the queue"""
        try:
            result = self.databases.list_documents(
                self.db_id,
                self.queue_id,
                [
                    Query.equal("status", "pending"),
                    Query.order_asc("created_at"),
                    Query.limit(1)
                ]
            )
            if result['total'] > 0:
                return result['documents'][0]
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
                        "user": parts[2],
                        "pass": parts[3]
                    }
        except Exception as e:
            print(f"[Appwrite] Error fetching proxy: {e}")
        return None

    def report_proxy_usage(self, proxy_id, success=True):
        """Increment usage or mark as failed"""
        try:
            doc = self.databases.get_document(self.db_id, self.proxy_id, proxy_id)
            data = {"last_used": datetime.now().isoformat()}
            if success:
                data["usage_count"] = (doc.get("usage_count", 0) or 0) + 1
            else:
                data["status"] = "failed"
            self.databases.update_document(self.db_id, self.proxy_id, proxy_id, data)
        except Exception as e:
            print(f"[Appwrite] Error reporting proxy: {e}")

    def update_status(self, doc_id, status, result_url=None, logs=None, screenshot_path=None, cookies_json=None):
        """Update the status and upload assets"""
        data = {"status": status}
        if result_url: data["result_url"] = result_url
        if logs: data["logs"] = logs[:5000]
        
        try:
            # Upload Screenshot
            if screenshot_path and os.path.exists(screenshot_path):
                file_result = self.storage.create_file(
                    self.bucket_id,
                    f"shot_{doc_id}",
                    InputFile.from_path(screenshot_path)
                )
                data["screenshot_id"] = file_result['$id']

            # Upload Cookies
            if cookies_json:
                cookie_path = f"tmp_cookies_{doc_id}.json"
                with open(cookie_path, 'w') as f:
                    json.dump(cookies_json, f)
                file_result = self.storage.create_file(
                    self.bucket_id,
                    f"cookies_{doc_id}",
                    InputFile.from_path(cookie_path)
                )
                data["cookie_file_id"] = file_result['$id']
                os.remove(cookie_path)

            self.databases.update_document(self.db_id, self.queue_id, doc_id, data)
            print(f"[Appwrite] Updated {doc_id} to {status}")
        except Exception as e:
            print(f"[Appwrite] Error updating status: {e}")

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
