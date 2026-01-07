"""
Main Worker Loop for Heroku (Optimized with Persistent Browser)
================================================================
Polls Appwrite for tasks and executes the OTP flow.
Optimizations:
- Browser session persists across multiple numbers (HUGE speed improvement)
- Only restarts browser on crash or every 50 numbers
- Batch logs locally and send once with final status update
"""

import os
import time
import sys
from datetime import datetime
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

def log_entry(msg):
    """Create timestamped log entry"""
    ts = datetime.now().strftime("%H:%M:%S")
    return f"[{ts}] {msg}"

# Global persistent browser instance
persistent_bot = None
numbers_processed = 0
MAX_NUMBERS_BEFORE_RESTART = 50

def get_browser(proxy_config):
    """Get or create persistent browser instance"""
    global persistent_bot, numbers_processed
    
    # Create new browser if needed
    if persistent_bot is None or persistent_bot.driver is None:
        print("[*] Creating NEW browser instance...", flush=True)
        persistent_bot = FacebookOTPBrowser(headless=True)
        persistent_bot.PROXY_CONFIG = proxy_config
        if not persistent_bot._setup_driver():
            print("[!] Failed to setup browser", flush=True)
            persistent_bot = None
            return None
        numbers_processed = 0
        print("[*] Browser ready.", flush=True)
    else:
        # Update proxy config (though IP rotates on proxy side anyway)
        persistent_bot.PROXY_CONFIG = proxy_config
    
    return persistent_bot

def cleanup_browser():
    """Force close browser"""
    global persistent_bot, numbers_processed
    try:
        if persistent_bot and persistent_bot.driver:
            persistent_bot.driver.quit()
    except: pass
    persistent_bot = None
    numbers_processed = 0

def main():
    global persistent_bot, numbers_processed
    print(f"[*] Worker started (Persistent Browser Mode). Polling Appwrite at {ENDPOINT}...", flush=True)
    
    while True:
        try:
            # 1. Look for pending task
            task = worker.get_pending_number()
            
            if task:
                doc_id = task['$id']
                phone = task['phone']
                print(f"\n[+] Processing: {phone} (Session count: {numbers_processed})")
                
                # Local log buffer
                logs = []
                logs.append(log_entry("🚀 Started processing"))
                
                # Mark as processing immediately
                worker.update_status(doc_id, "processing")
                
                try:
                    # 2. Get Best Proxy
                    proxy = worker.get_best_proxy()
                    if not proxy:
                        print("[!] No active proxies available in pool!")
                        logs.append(log_entry("❌ No active proxies available"))
                        worker.update_status(doc_id, "failed", error_reason="NO_PROXIES", logs="\n".join(logs))
                        continue
                    
                    logs.append(log_entry(f"🌐 Using proxy: {proxy['host']}"))
                    print(f"[*] Using Proxy: {proxy['host']}")
                    
                    # 3. Get or reuse browser
                    bot = get_browser(proxy)
                    if not bot:
                        logs.append(log_entry("❌ Browser failed to start"))
                        worker.update_status(doc_id, "failed", error_reason="BROWSER_FAIL", logs="\n".join(logs))
                        continue
                    
                    try:
                        # 4. Clear cookies and run flow (reusing browser)
                        try:
                            bot.driver.delete_all_cookies()
                        except: pass
                        
                        logs.append(log_entry("🔧 Running flow (reusing browser)..."))
                        flow_result = bot.run_flow_reuse(phone)  # Uses existing browser
                        
                        if flow_result:
                            print("[✓] Flow successful!", flush=True)
                            logs.append(log_entry("✅ OTP sent successfully!"))
                            
                            try:
                                worker.report_proxy_usage(proxy['id'], True)
                            except: pass
                            
                            # PHASE 1: Immediate Success Status Update
                            try:
                                worker.update_status(doc_id, "success", logs="\n".join(logs))
                            except Exception as e:
                                print(f"[FATAL] Phase 1 Update Failed: {e}", flush=True)

                            # PHASE 2: Fetch and Upload Assets
                            screenshot = None
                            cookies = None
                            result_url = None
                            
                            try:
                                files = os.listdir('.')
                                shots = sorted([f for f in files if f.startswith('step_success')], reverse=True)
                                if shots: screenshot = shots[0]
                            except: pass
                            
                            try:
                                # Retry mechanism for cookies (selenium-wire sometimes has connection issues)
                                import time
                                cookies = None
                                result_url = None
                                for attempt in range(3):
                                    try:
                                        time.sleep(0.5)  # Small delay to stabilize connection
                                        cookies = bot.driver.get_cookies()
                                        result_url = bot.driver.current_url
                                        logs.append(log_entry(f"📦 Saved {len(cookies)} cookies"))
                                        break
                                    except Exception as retry_err:
                                        if attempt < 2:
                                            logs.append(log_entry(f"⚠️ Cookie retry {attempt+1}/3..."))
                                            time.sleep(1)
                                        else:
                                            raise retry_err
                            except Exception as e:
                                logs.append(log_entry(f"⚠️ Could not get cookies: {str(e)[:50]}"))
                            
                            # Update with assets
                            try:
                                worker.update_status(
                                    doc_id, 
                                    "success", 
                                    result_url=result_url,
                                    screenshot_path=screenshot,
                                    cookies_json=cookies,
                                    logs="\n".join(logs)
                                )
                            except: pass
                            
                            if screenshot: 
                                try: os.remove(screenshot)
                                except: pass
                            
                            numbers_processed += 1
                        else:
                            # Flow failed
                            print("[X] Flow failed", flush=True)
                            logs.append(log_entry("❌ Flow failed - SMS not found or verify error"))
                            
                            # Get screenshot
                            screenshot = None
                            try:
                                files = os.listdir('.')
                                shots = sorted([f for f in files if f.startswith('step_')], reverse=True)
                                if shots: screenshot = shots[0]
                            except: pass
                            
                            worker.update_status(doc_id, "failed", error_reason="FLOW_FAILED", screenshot_path=screenshot, logs="\n".join(logs))
                            worker.report_proxy_usage(proxy['id'], False)
                            
                            if screenshot: 
                                try: os.remove(screenshot)
                                except: pass
                            
                            numbers_processed += 1
                                
                    except Exception as flow_err:
                        print(f"[!] Browser/Flow Error: {flow_err}", flush=True)
                        logs.append(log_entry(f"⚠️ Error: {str(flow_err)[:100]}"))
                        worker.update_status(doc_id, "failed", error_reason=f"ERROR: {str(flow_err)[:50]}", logs="\n".join(logs))
                        
                        # Browser crashed - force cleanup
                        cleanup_browser()
                        
                except Exception as task_err:
                    print(f"[!] Task Error: {task_err}", flush=True)
                    logs.append(log_entry(f"💥 Crashed: {str(task_err)[:100]}"))
                    worker.update_status(doc_id, "failed", error_reason=f"CRASH: {str(task_err)[:50]}", logs="\n".join(logs))
                
                # Check if we need to restart browser after N numbers
                if numbers_processed >= MAX_NUMBERS_BEFORE_RESTART:
                    print(f"[*] Processed {numbers_processed} numbers, restarting browser for freshness...", flush=True)
                    cleanup_browser()
            
            else:
                # No tasks, sleep
                time.sleep(10)
                
        except Exception as e:
            print(f"[!] Loop Error: {e}", flush=True)
            cleanup_browser()  # Cleanup on any major error
            time.sleep(30)

if __name__ == "__main__":
    main()
