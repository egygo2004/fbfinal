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
                worker.append_log(doc_id, "🚀 Started processing")
                
                try:
                    success = False
                    retry_count = 0
                    max_retries = 3
                    
                    while not success and retry_count < max_retries:
                        # 2. Get Best Proxy
                        proxy = worker.get_best_proxy()
                        if not proxy:
                            print("[!] No active proxies available in pool!")
                            worker.append_log(doc_id, "❌ No active proxies available")
                            worker.update_status(doc_id, "failed", error_reason="NO_PROXIES")
                            break
                        
                        worker.append_log(doc_id, f"🌐 Using proxy: {proxy['host']} (attempt {retry_count+1})")
                        print(f"[*] Using Proxy: {proxy['host']} (Try {retry_count+1})")
                        
                        # 3. Run Flow
                        bot = FacebookOTPBrowser(headless=True)
                        bot.PROXY_CONFIG = proxy
                        
                        try:
                            worker.append_log(doc_id, "🔧 Setting up browser...")
                            flow_result = bot.run_flow(phone)
                            
                            if flow_result:
                                success = True
                                print("[✓] Flow successful!")
                                worker.append_log(doc_id, "✅ OTP sent successfully!")
                                worker.report_proxy_usage(proxy['id'], True)
                                
                                # Finalize assets - wrap in try-except
                                screenshot = None
                                cookies = None
                                result_url = None
                                
                                try:
                                    files = os.listdir('.')
                                    shots = sorted([f for f in files if f.startswith('step_success')], reverse=True)
                                    if shots: screenshot = shots[0]
                                except: pass
                                
                                try:
                                    cookies = bot.driver.get_cookies()
                                    result_url = bot.driver.current_url
                                except Exception as e:
                                    print(f"[!] Could not get cookies/URL: {e}")
                                
                                worker.append_log(doc_id, "📦 Saving cookies and screenshot...")
                                print(f"[*] Calling update_status with status=success")
                                
                                worker.update_status(
                                    doc_id, 
                                    "success", 
                                    result_url=result_url,
                                    screenshot_path=screenshot,
                                    cookies_json=cookies
                                )
                                print(f"[*] update_status completed!")
                                
                                if screenshot: 
                                    try: os.remove(screenshot)
                                    except: pass
                            else:
                                print("[X] Flow failed (SMS not found or logic error)")
                                worker.append_log(doc_id, "❌ Flow returned false - updating status to failed")
                                
                                # Get last screenshot for failed cases
                                screenshot = None
                                files = os.listdir('.')
                                shots = sorted([f for f in files if f.startswith('step_')], reverse=True)
                                if shots: screenshot = shots[0]
                                
                                print(f"[*] Updating status to failed with screenshot: {screenshot}")
                                worker.update_status(doc_id, "failed", error_reason="FLOW_FAILED", screenshot_path=screenshot)
                                print("[*] Status updated to failed!")
                                if screenshot: 
                                    try: os.remove(screenshot)
                                    except: pass
                                break
                                
                        except Exception as flow_err:
                            print(f"[!] Browser/Proxy Error: {flow_err}")
                            worker.append_log(doc_id, f"⚠️ Error: {str(flow_err)[:100]}")
                            worker.report_proxy_usage(proxy['id'], False)
                            retry_count += 1
                            time.sleep(2)
                        finally:
                            try: bot.driver.quit()
                            except: pass
                            
                except Exception as task_err:
                    # Catch-all to ensure status is updated
                    print(f"[!] Task Error: {task_err}")
                    worker.append_log(doc_id, f"💥 Crashed: {str(task_err)[:100]}")
                    worker.update_status(doc_id, "failed", error_reason=f"CRASH: {str(task_err)[:50]}")
            
            else:
                # No tasks, sleep
                time.sleep(10)
                
        except Exception as e:
            print(f"[!] Loop Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
