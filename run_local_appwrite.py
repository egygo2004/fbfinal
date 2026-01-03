"""
Local Appwrite Worker - Mirrors Heroku Behavior
================================================
Fetches proxies from Appwrite DB, checks IP, and runs OTP flow.
Use for local testing with production-like behavior.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fb_otp_browser import FacebookOTPBrowser
from appwrite_worker import AppwriteWorkerClient

# Appwrite Credentials (same as Heroku)
ENDPOINT = os.environ.get("APPWRITE_ENDPOINT", "https://fra.cloud.appwrite.io/v1")
PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID", "finalfb")
API_KEY = os.environ.get("APPWRITE_API_KEY", "standard_ab59cd2a796312ebf0d2c7ce1b3316c845f05f81afb94eaf4de25b562ee94564da2946616819f3604b36b58c60f5899541648efe9d2b5e3a0a3a9469a19464f36d995a9afbe3bb62b7e5eb33b7e5b78269f0bbda197f862a836eaec6fbafe886226fae4f9caf6a866da99e2327d5f68770c9d203c0868fe34b5f0a36f8229b4b")

def main():
    print("=" * 50)
    print("🧪 LOCAL APPWRITE WORKER TEST")
    print("=" * 50)
    
    # Initialize Appwrite client
    print("\n[1] Connecting to Appwrite...")
    worker = AppwriteWorkerClient(ENDPOINT, PROJECT_ID, API_KEY)
    print("    ✅ Connected!")
    
    # Get best proxy from Appwrite
    print("\n[2] Fetching proxy from Appwrite DB...")
    proxy = worker.get_best_proxy()
    if not proxy:
        print("    ❌ No active proxies available!")
        return
    print(f"    ✅ Using Proxy: {proxy['host']}:{proxy['port']}")
    print(f"       User: {proxy['username'][:10]}...")
    
    # Get test phone number
    phone = input("\n[3] Enter phone number to test: ").strip()
    if not phone:
        phone = "+201066373802"  # Default test number
    print(f"    📱 Testing: {phone}")
    
    # Choose headless mode
    headless_input = input("\n[4] Run headless? (y/n, default=n): ").strip().lower()
    headless = headless_input == 'y'
    print(f"    🖥️ Headless: {headless}")
    
    # Initialize browser with the proxy from Appwrite
    print("\n[5] Starting browser...")
    bot = FacebookOTPBrowser(headless=headless)
    bot.PROXY_CONFIG = proxy  # Inject selected proxy (same as Heroku)
    
    # Run flow
    print("\n[6] Running OTP flow...")
    print("-" * 50)
    result = bot.run_flow(phone)
    print("-" * 50)
    
    if result:
        print("\n🎉 SUCCESS! OTP was sent.")
        print(f"    📱 URL: {bot.driver.current_url}")
        cookies = bot.driver.get_cookies()
        print(f"    🍪 Cookies: {len(cookies)} items")
        import json
        print(json.dumps(cookies, indent=2))
        bot.driver.quit()
    else:
        print("\n❌ FAILED. Check logs above.")

if __name__ == "__main__":
    main()
