"""Test opening cookies with URL"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

# Cookies from the last run
COOKIES = [
  {"domain": ".facebook.com", "httpOnly": True, "name": "fr", "path": "/", "sameSite": "None", "secure": True, "value": "0VcW7TOLARIUzf5LN..BpWZLi..AAA.0.0.BpWZLq.AWegK8qlps-YUpPlLRteGWA48O8"},
  {"domain": ".facebook.com", "httpOnly": True, "name": "sfiu", "path": "/", "sameSite": "None", "secure": True, "value": "AYhmxaBwZY7xKP-p_RslhOVPKKJha1Y0hiRrgq5b64l8YbG8tynDxwBtEQPAOefpnkPQG7Iq6sXNK-k1nc4sm9kUTJmh2eHxY78K-vhw32yP_iKAWQ9t3Po6BBdr7Cf7yWx9EDAEm7aMq8q37exIUlauT0rEVUP_WPwc26za24XQhMJ5DprktXKzQuSvgKE1Nhu4Gbu5L0MVxSRUG4DSsLO60Y6oteEHbvSzuihTRXgjwg"},
  {"domain": ".facebook.com", "httpOnly": True, "name": "ps_l", "path": "/", "sameSite": "Lax", "secure": True, "value": "1"},
  {"domain": ".facebook.com", "httpOnly": True, "name": "ps_n", "path": "/", "sameSite": "None", "secure": True, "value": "1"},
  {"domain": ".facebook.com", "httpOnly": True, "name": "sb", "path": "/", "sameSite": "None", "secure": True, "value": "5JJZaX6n3mFXjhFmW5vdOWgn"},
  {"domain": ".facebook.com", "httpOnly": False, "name": "wd", "path": "/", "sameSite": "Lax", "secure": True, "value": "2048x1152"},
  {"domain": ".facebook.com", "httpOnly": False, "name": "m_pixel_ratio", "path": "/", "sameSite": "Lax", "secure": True, "value": "1"},
  {"domain": ".facebook.com", "httpOnly": True, "name": "datr", "path": "/", "sameSite": "None", "secure": True, "value": "4pJZaZ4_N57rMd1cxzDU6JwM"}
]

URL = "https://mbasic.facebook.com/recover/code/?ph%5B0%5D=%2B%2A%2A%2A%2A%2A%2A%2A%2A%2A%2A34&rm=send_sms&c=%2Flogin%2F&hash=AUZAzWeoJhjfZT-03rU&_rdr"

print("[*] Opening browser with cookies...")

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# First go to facebook to set cookies
driver.get("https://mbasic.facebook.com")
time.sleep(2)

# Add cookies
print("[*] Adding cookies...")
for cookie in COOKIES:
    try:
        # Remove expiry if it exists (might be expired)
        if 'expiry' in cookie:
            del cookie['expiry']
        driver.add_cookie(cookie)
        print(f"   [+] {cookie['name']}")
    except Exception as e:
        print(f"   [-] {cookie['name']}: {e}")

# Navigate to URL
print(f"\n[*] Opening URL: {URL[:60]}...")
driver.get(URL)

print("\n[OK] Done! Check the browser.")
input("Press Enter to close...")
driver.quit()
