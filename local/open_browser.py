"""
Open Browser with Data Saver Settings (for manual testing)
"""
import sys
import os
import time

try:
    from seleniumwire import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    print("[OK] Libraries imported")
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    sys.exit(1)

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

# SOAX Proxy Configuration
PROXY_CONFIG = {
    'host': 'proxy.soax.com',
    'port': '9000',
    'username': 'nNcDyyf3PiC2OX3p',
    'password': 'mobile;us;'
}

def open_browser():
    print("[INFO] Setting up Chrome browser (DATA SAVER MODE)...")
    options = Options()
    
    # Old mobile user agent
    old_mobile_ua = "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 5 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36"
    
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={old_mobile_ua}")
    options.add_argument("--window-size=360,640")
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=en-US")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors=yes")
    
    # DATA SAVING OPTIONS
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-remote-fonts")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disk-cache-size=0")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-default-apps")
    
    # Experimental options
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2,
        "profile.managed_default_content_settings.plugins": 2,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Configure proxy
    proxy = PROXY_CONFIG
    proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
    
    seleniumwire_options = {
        'proxy': {
            'http': proxy_url,
            'https': proxy_url,
            'no_proxy': 'localhost,127.0.0.1'
        },
        'verify_ssl': False,
        'connection_timeout': 60,
        'request_timeout': 60
    }
    
    print(f"[OK] SOAX Proxy configured: {proxy['host']}:{proxy['port']}")

    try:
        if ChromeDriverManager:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options, seleniumwire_options=seleniumwire_options)
        else:
            driver = webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)
        
        # CDP URL blocking
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.setBlockedURLs", {
            "urls": [
                "*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.svg", "*.ico", "*.bmp",
                "*.css", "*.woff", "*.woff2", "*.ttf", "*.eot", "*.otf",
                "*.mp4", "*.webm", "*.mp3", "*.wav",
                "*google-analytics*", "*googletagmanager*", "*facebook.com/tr*",
                "*pixel*", "*analytics*", "*tracking*", "*beacon*",
                "*connect.facebook.net*", "*/ajax/bz*",
                "*rsrc.php/v3*", "*rsrc.php/v4*"
            ]
        })
        print("[OK] CDP URL blocking enabled")
        
        # Anti-detect
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        })
        
        driver.set_page_load_timeout(120)
        
        print("[OK] Chrome browser ready!")
        print("\n" + "="*50)
        print(" Browser is open - test manually!")
        print(" Opening mbasic.facebook.com/login/identify...")
        print("="*50 + "\n")
        
        # Open Facebook recovery page
        driver.get('https://mbasic.facebook.com/login/identify/?ctx=recover')
        
        print("[INFO] Press ENTER to close browser when done...")
        input()
        
        driver.quit()
        print("[OK] Browser closed")
        
    except Exception as e:
        print(f"[ERROR] Failed: {e}")

if __name__ == "__main__":
    open_browser()
