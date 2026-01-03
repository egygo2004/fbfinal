"""
Main Worker Loop for Heroku
===========================
Polls Appwrite for tasks and executes the OTP flow.
"""

import os
import time
import sys
from fb_otp_browser import FacebookOTPBrowser
from appwrite_worker import AppwriteWorkerClient

# Load Credentials from Environment
ENDPOINT = os.environ.get("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")
API_KEY = os.environ.get("APPWRITE_API_KEY")

print("[DEBUG] main_worker: Imports complete.", flush=True)

timeout_start = time.time()
while not PROJECT_ID or not API_KEY:
    if time.time() - timeout_start > 5:
        print("[FATAL] Appwrite credentials missing. Set APPWRITE_PROJECT_ID and APPWRITE_API_KEY.", flush=True)
        sys.exit(1)
    time.sleep(1)

print("[DEBUG] main_worker: Credentials found. Initializing Client...", flush=True)
try:
    worker = AppwriteWorkerClient(ENDPOINT, PROJECT_ID, API_KEY)
    print("[DEBUG] main_worker: Client initialized.", flush=True)
except Exception as e:
    print(f"[FATAL] Client init failed: {e}", flush=True)
    sys.exit(1)

def main():
    print(f"[*] Worker started. Polling Appwrite at {ENDPOINT}...", flush=True)
    
    while True:
        try:
            # 1. Look for pending task
            task = worker.get_pending_number()
            
            if task:
                doc_id = task['$id']
                phone = task['phone']
                print(f"\n[+] Processing: {phone}")
                worker.update_status(doc_id, "processing")
                
                success = False
                retry_count = 0
                max_retries = 3 # Try with up to 3 different proxies
                
                while not success and retry_count < max_retries:
                    # 2. Get Best Proxy
                    proxy = worker.get_best_proxy()
                    if not proxy:
                        print("[!] No active proxies available in pool!")
                        worker.update_status(doc_id, "failed", logs="No active proxies available")
                        break
                    
                    print(f"[*] Using Proxy: {proxy['host']} (Try {retry_count+1})")
                    
                    # 3. Run Flow
                    bot = FacebookOTPBrowser(headless=True)
                    bot.PROXY_CONFIG = proxy # Inject selected proxy
                    
                    try:
                        flow_result = bot.run_flow(phone)
                        if flow_result:
                            success = True
                            print("[✓] Flow successful!")
                            worker.report_proxy_usage(proxy['id'], True)
                            
                            # Finalize assets
                            screenshot = None
                            files = os.listdir('.')
                            shots = sorted([f for f in files if f.startswith('step_success')], reverse=True)
                            if shots: screenshot = shots[0]
                            
                            cookies = bot.driver.get_cookies() # Get fresh cookies from driver

                            worker.update_status(
                                doc_id, 
                                "success", 
                                result_url=bot.driver.current_url,
                                screenshot_path=screenshot,
                                cookies_json=cookies
                            )
                            if screenshot: os.remove(screenshot)
                        else:
                            print("[X] Flow failed (SMS not found or logic error)")
                            # We don't necessarily mark proxy as failed here unless it's a connection issue
                            # But for "Free Trial" rotation, we might want to rotate if it fails too often
                            worker.update_status(doc_id, "failed", logs="SMS option not found")
                            break # Don't retry different proxies if it's just a Facebook logic failure
                            
                    except Exception as flow_err:
                        print(f"[!] Browser/Proxy Error: {flow_err}")
                        worker.report_proxy_usage(proxy['id'], False) # Mark as FAILED
                        retry_count += 1
                        time.sleep(2)
                    finally:
                        try: bot.driver.quit()
                        except: pass
            
            else:
                # No tasks, sleep
                time.sleep(10)
                
        except Exception as e:
            print(f"[!] Loop Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
