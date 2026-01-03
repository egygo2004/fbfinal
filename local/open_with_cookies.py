"""
Open Facebook URL with saved cookies
Usage: python open_with_cookies.py <cookies_file.json> <url>
"""
import sys
import json
import time

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
except ImportError:
    print("Please install: pip install selenium")
    sys.exit(1)

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

def open_with_cookies(cookies_file, url):
    # Load cookies
    try:
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
        print(f"[OK] Loaded {len(cookies)} cookies from {cookies_file}")
    except Exception as e:
        print(f"[ERROR] Could not load cookies: {e}")
        return
    
    # Ensure mbasic URL
    url = url.replace("www.facebook.com", "mbasic.facebook.com")
    url = url.replace("m.facebook.com", "mbasic.facebook.com")
    
    print(f"[INFO] Opening URL: {url}")
    
    options = Options()
    
    # Mobile user agent
    mobile_ua = "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 5 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36"
    
    options.add_argument(f"user-agent={mobile_ua}")
    options.add_argument("--window-size=400,700")
    options.add_argument("--disable-notifications")
    
    try:
        if ChromeDriverManager:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)
        
        # First go to facebook domain to set cookies
        driver.get("https://mbasic.facebook.com")
        time.sleep(2)
        
        # Add cookies
        for cookie in cookies:
            try:
                # Remove problematic fields
                cookie.pop('sameSite', None)
                cookie.pop('expiry', None)
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"[WARN] Could not add cookie {cookie.get('name', 'unknown')}: {e}")
        
        print(f"[OK] Cookies added successfully")
        
        # Now go to the target URL
        driver.get(url)
        time.sleep(2)
        
        print(f"[OK] Browser opened!")
        print(f"[INFO] Current URL: {driver.current_url}")
        print("\n" + "="*50)
        print(" Press ENTER to close browser")
        print("="*50)
        input()
        
        driver.quit()
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python open_with_cookies.py <cookies_file.json> <facebook_url>")
        print('Example: python open_with_cookies.py cookies_959750797929.json "https://mbasic.facebook.com/recover/code/..."')
    else:
        open_with_cookies(sys.argv[1], sys.argv[2])
