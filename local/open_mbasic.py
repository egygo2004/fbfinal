"""
Open any Facebook URL as mbasic (mobile basic)
Usage: python open_mbasic.py "https://facebook.com/..." 
"""
import sys
import os

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

def open_as_mbasic(url):
    # Convert any facebook.com URL to mbasic
    url = url.replace("www.facebook.com", "mbasic.facebook.com")
    url = url.replace("m.facebook.com", "mbasic.facebook.com")
    
    print(f"[INFO] Opening URL: {url}")
    
    options = Options()
    
    # Old mobile user agent - forces mbasic version
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
        
        driver.get(url)
        
        print("[OK] Browser opened!")
        print(f"[INFO] Current URL: {driver.current_url}")
        print("\n" + "="*50)
        print(" Press ENTER to close browser")
        print("="*50)
        input()
        
        driver.quit()
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python open_mbasic.py <facebook_url>")
        print('Example: python open_mbasic.py "https://mbasic.facebook.com/recover/code/..."')
    else:
        open_as_mbasic(sys.argv[1])
