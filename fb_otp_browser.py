"""
Facebook OTP Browser Automation (Heroku Production Optimized)
=============================================================
Uses Selenium with Decodo Sticky Proxy and Extreme Data Saving.
Optimized for mbasic.facebook.com and cloud environments.

Features:
- Decodo Sticky Proxy Integrated
- 'Eager' page loading + window.stop() for ultra-low data
- CDP & Request Interception (blocking Google/Autofill/Optimization)
- Robust mbasic flow with 'Try another way' handling
- Cookie export & Appwrite ready (placeholder)
"""

import sys
import os
import time
import re
import random
import threading
from datetime import datetime
import json
import requests
import io
import zipfile
import tempfile
import traceback

# Fix console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from seleniumwire import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    print("[DEBUG] Essential libraries imported successfully (with seleniumwire).", flush=True)
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    sys.exit(1)

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

# Colors (Minimal for logs)
class C:
    CYAN = '\033[96m'
    G = '\033[92m'
    Y = '\033[93m'
    R = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def log(msg, level="INFO"):
    t = datetime.now().strftime("%H:%M:%S")
    colors = {"INFO": C.CYAN, "OK": C.G, "WARN": C.Y, "ERROR": C.R, "SUCCESS": C.G + C.BOLD}
    c = colors.get(level, "")
    print(f"[{t}] {c}[{level}] {msg}{C.END}", flush=True)

class FacebookOTPBrowser:
    # Sticky Proxy Configuration (Decodo US)
    PROXY_CONFIG = {
        'host': 'us.decodo.com',
        'port': '10001',
        'username': 'user-spzpdyn003-sessionduration-1',
        'password': 'S~wXakn3z89xeZw0Ps'
    }
    
    def __init__(self, headless=True):
        self.driver = None
        self.headless = headless
        self.wait_time = 20
        self.current_phone = None
        self.telegram_token = os.environ.get("TELEGRAM_TOKEN")
        self.telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

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
        
        # 2. Chrome Binary Detection (Robust)
        chrome_bin = os.environ.get("GOOGLE_CHROME_BIN")
        if not chrome_bin:
            for p in ["/app/.chrome-for-testing/chrome-linux64/chrome", "/app/.apt/usr/bin/google-chrome", "/usr/bin/google-chrome"]:
                if os.path.exists(p):
                    chrome_bin = p
                    break
        if chrome_bin:
            options.binary_location = chrome_bin
            log(f"Using Chrome Binary: {chrome_bin}")

        # 3. Aggressive Data Saving & Background Traffic Blocking
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

        # 4. User Agent & Window
        old_mobile_ua = "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 5 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36"
        options.add_argument(f"user-agent={old_mobile_ua}")
        options.add_argument("--window-size=360,640")
        options.add_argument("--lang=en-US")
        
        # 5. SSL Handling
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors=yes")
        
        # 6. Experimental Preferences
        options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.fonts": 2,
            "profile.managed_default_content_settings.plugins": 2,
            "profile.managed_default_content_settings.javascript": 1,  # Keep enabled but block external
        })
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 7a. Block external JavaScript files (keep inline)
        options.add_argument("--disable-javascript-harmony-shipping")

        # 7. Page Load Strategy (NONE - fastest, we control loading)
        options.page_load_strategy = 'none'
        log("🚀 Page load strategy: NONE (ultra-fast)", "OK")

        # 8. Proxy Connection
        proxy = self.PROXY_CONFIG
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

        # 9. Initialize WebDriver
        try:
            # Priority order for chromedriver:
            # 1. CHROMEDRIVER_PATH environment variable
            # 2. Chrome for Testing path (Heroku buildpack)
            # 3. webdriver_manager (local development)
            driver_path = os.environ.get("CHROMEDRIVER_PATH")
            chrome_for_testing_driver = "/app/.chrome-for-testing/chromedriver-linux64/chromedriver"
            
            service = None
            if driver_path and os.path.exists(driver_path):
                log(f"Using Chromedriver: {driver_path}")
                os.chmod(driver_path, 0o755)
                service = Service(driver_path)
            elif os.path.exists(chrome_for_testing_driver):
                log(f"Using Chrome for Testing driver: {chrome_for_testing_driver}")
                os.chmod(chrome_for_testing_driver, 0o755)
                service = Service(chrome_for_testing_driver)
            elif ChromeDriverManager:
                log("Using webdriver_manager (local)")
                service = Service(ChromeDriverManager().install())
            else:
                service = Service()

            # Debug Proxy Config
            if self.PROXY_CONFIG:
                sanitized = self.PROXY_CONFIG.copy()
                if 'password' in sanitized: sanitized['password'] = '***'
                log(f"Configuring Proxy: {sanitized}")

            self.driver = webdriver.Chrome(service=service, options=options, seleniumwire_options=seleniumwire_options)
            
            # 10. Request Interceptor (SeleniumWire level)
            def request_interceptor(request):
                blocked_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.wasm', '.woff', '.woff2', '.ttf', '.css', '.mp4', '.svg', '.ico', '.webp')
                blocked_domains = (
                    # Analytics & Tracking
                    'google-analytics', 'googletagmanager', 'pixel', 'ads', 'tracking', 'facebook.com/tr',
                    # Google Services (unnecessary)
                    'accounts.google.com', 'android.clients.google.com', 'www.google.com',
                    'optimizationguide-pa.googleapis.com', 'content-autofill.googleapis.com',
                    'clients2.google.com', 'clients1.google.com', 'clients.google.com',
                    'mtalk.google.com', 'play.google.com', 'update.googleapis.com',
                    'safebrowsing.googleapis.com', 'ssl.gstatic.com', 'fonts.googleapis.com',
                    'fonts.gstatic.com', 'apis.google.com', 'translate.googleapis.com',
                    # Facebook Static (CSS/Images)
                    'static.xx.fbcdn.net', 'static.cdninstagram.com', 'scontent',
                    'fbsbx.com', 'fbcdn.net/rsrc', 'connect.facebook.net'
                )
                url = request.url.lower()
                # Block by extension
                if any(url.endswith(ext) for ext in blocked_extensions):
                    request.abort()
                    return
                # Block by domain
                if any(d in url for d in blocked_domains):
                    request.abort()
                    return
                # Block FB resource files (CSS, JS bundles) except bootloader
                if 'rsrc.php' in url and 'bootloader' not in url:
                    request.abort()
                    return

            self.driver.request_interceptor = request_interceptor
            log("🛡️ Interceptor Active", "OK")
            
            # 11. CDP Network Blocking (Chrome level)
            try:
                self.driver.execute_cdp_cmd("Network.enable", {})
                self.driver.execute_cdp_cmd("Network.setBlockedURLs", {
                    "urls": [
                        # Static assets
                        "*.png", "*.jpg", "*.jpeg", "*.gif", "*.css", "*.woff", "*.woff2", "*.ico", "*.svg", "*.webp",
                        # Analytics
                        "*google-analytics*", "*googletagmanager*", "*pixel*",
                        # Google services
                        "*optimizationguide*", "*content-autofill*", "*mtalk.google.com*",
                        "*googleapis.com*", "*clients.google.com*", "*clients2.google.com*",
                        "*accounts.google.com*", "*android.clients.google.com*", "*www.google.com*",
                        "*safebrowsing*", "*gstatic.com*", "*translate.google*", "*play.google.com*",
                        # Facebook/Meta unnecessary
                        "*static.xx.fbcdn.net*", "*fbcdn.net/rsrc*", "*connect.facebook.net*",
                        "*scontent*", "*fbsbx.com*"
                        # Removed: *graphql*, *ajax/bz*, webrtc, websocket - needed for OTP
                    ]
                })
                log("🚫 CDP Traffic Blocked", "OK")
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
                })
            except: pass

            self.driver.set_page_load_timeout(180)
            self.driver.set_script_timeout(60)
            self.wait = WebDriverWait(self.driver, 20)
            return True
        except Exception as e:
            log(f"Setup Error: {e}", "ERROR")
            traceback.print_exc()
            if self.driver: self.driver.quit()
            return False

    def _save_step_screenshot(self, step_name):
        try:
            filename = f"step_{step_name}_{int(time.time())}.png"
            self.driver.save_screenshot(filename)
            log(f"📸 Screenshot: {filename}", "INFO")
            return filename
        except: return None

    def send_telegram_photo(self, caption, file_path):
        if not self.telegram_token or not self.telegram_chat_id: return
        try:
            log("Sending Telegram photo...", "INFO")
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendPhoto"
            with open(file_path, "rb") as f:
                requests.post(url, files={"photo": f}, data={"chat_id": self.telegram_chat_id, "caption": caption}, timeout=10)
            log("Telegram photo sent!", "INFO")
        except Exception as e: log(f"Telegram error: {e}", "WARN")

    def check_ip(self):
        try:
            log("🌍 Checking IP...", "INFO")
            self.driver.get('https://api.ipify.org?format=json')
            time.sleep(2)
            ip_info = self.driver.find_element(By.TAG_NAME, "body").text
            log(f"✅ Current IP: {ip_info}", "SUCCESS")
        except Exception as e:
            log(f"⚠️ Could not verify IP: {e}", "WARN")

    def wait_for_ready(self, timeout=5):
        """Smart wait using document.readyState instead of fixed sleep"""
        try:
            for _ in range(timeout * 10):  # Check every 100ms
                state = self.driver.execute_script("return document.readyState")
                if state in ['complete', 'interactive']:
                    return True
                time.sleep(0.1)
        except:
            pass
        return False

    def run_flow(self, phone):
        self.current_phone = phone
        log(f"🚀 Processing: {phone}")
        if not self._setup_driver(): return False
        
        # Skip IP check for speed (uncomment for debugging)
        # self.check_ip()

        try:
            # 1. Open with DOM injection approach
            self.driver.get('https://mbasic.facebook.com/login/identify/?ctx=recover')
            self.wait_for_ready(3)  # Smart wait instead of fixed sleep
            self.driver.execute_script("window.stop();")
            log("🛑 Force Stopped Home Page", "OK")

            # 2. Search - use DOM injection for speed
            inp = WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((By.NAME, "email")))
            self.driver.execute_script("arguments[0].value = arguments[1];", inp, phone)  # DOM injection
            btn = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
            self.driver.execute_script("arguments[0].click();", btn)  # DOM click
            time.sleep(1.5)
            self.driver.execute_script("window.stop();")
            log("🛑 Force Stopped Post-Search", "OK")

            # ⚡ EARLY DETECTION - Check for account not found immediately
            time.sleep(1)
            quick_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            if "doesn't match" in quick_text or "try again or create" in quick_text or "no search results" in quick_text or "لم يتم العثور" in quick_text:
                log("⚡ Account NOT FOUND (early detection)", "WARN")
                return False

            # Continue normal flow
            self.wait_for_ready(2)
            
            # 3. Handle intermediate pages ("Try another way")
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            if "no search results" in page_text or "لم يتم العثور" in page_text or "doesn't match" in page_text:
                log("❌ Account NOT FOUND", "WARN")
                return False

            keywords = ["Try another way", "طريقة أخرى", "try another way", "Forgot password"]
            for kw in keywords:
                try:
                    btn = self.driver.find_element(By.PARTIAL_LINK_TEXT, kw)
                    btn.click()
                    time.sleep(1.5)
                    self.driver.execute_script("window.stop();")
                    log(f"Clicked: {kw}", "OK")
                    break
                except: continue

            # 4. Selection - IMPROVED with phone number matching
            self.driver.execute_script("window.stop();")
            self._save_step_screenshot("3_selection")
            
            # Get last 2 digits for matching
            phone_last_2 = phone[-2:] if phone else ""
            log(f"Phone last 2 digits: {phone_last_2}", "INFO")
            
            sms_found = False
            best_match_radio = None
            
            # Check Radios with phone matching
            radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            for r in radios:
                try:
                    parent = r.find_element(By.XPATH, "./..")
                    grandparent = parent.find_element(By.XPATH, "./..")
                    full_text = f"{parent.text.lower()} {grandparent.text.lower()}"
                    
                    is_sms = "sms" in full_text or "send code via sms" in full_text
                    matches_phone = phone_last_2 and phone_last_2 in full_text
                    
                    if is_sms and matches_phone:
                        self.driver.execute_script("arguments[0].click();", r)
                        sms_found = True
                        log(f"✅ SMS option matching phone {phone_last_2} selected", "OK")
                        break
                    elif is_sms and not best_match_radio:
                        best_match_radio = r
                except: pass
            
            # Use fallback SMS if no exact match
            if not sms_found and best_match_radio:
                self.driver.execute_script("arguments[0].click();", best_match_radio)
                sms_found = True
                log("SMS radio selected (fallback)", "OK")
            
            if not sms_found: # Fallback text click
                clickable = self.driver.find_elements(By.CSS_SELECTOR, "div[role='button'], span, label, a")
                for el in clickable:
                    el_text = el.text.lower()
                    if ("sms" in el_text or "send code via sms" in el_text) and (phone_last_2 in el_text or not phone_last_2):
                        try:
                            el.click()
                            sms_found = True
                            log("SMS text selected", "OK")
                            break
                        except: continue
            
            if not sms_found:
                log("❌ SMS Option NOT FOUND", "ERROR")
                return False

            # Submit Selection
            time.sleep(1)
            btns = self.driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            for btn in btns:
                if any(x in btn.text.lower() for x in ["continue", "send", "متابعة", "إرسال"]):
                    btn.click()
                    time.sleep(2)
                    self.driver.execute_script("window.stop();")
                    log("🛑 Force Stopped Final", "OK")
                    break

            # 5. Result
            current_url = self.driver.current_url
            if "recover/code" in current_url or "enter code" in self.driver.page_source.lower():
                log("🎉 SUCCESS: OTP SENT!", "SUCCESS")
                log(f"📱 URL: {current_url}")
                
                # Snapshot and Cookie placeholder for Appwrite
                shot = self._save_step_screenshot("success")
                cookies = self.driver.get_cookies()
                # Telegram removed as per request
                return True
            else:
                log("Failed to verify OTP sent", "ERROR")
                self._save_step_screenshot("fail_verify")
                return False

        except Exception as e:
            log(f"Flow Error: {e}", "ERROR")
            if self.driver:
                try: self.driver.quit()
                except: pass
            return False
        # Note: driver.quit() is NOT called on success - main_worker handles it

    def run_flow_reuse(self, phone):
        """Run flow using existing browser instance (for speed optimization)"""
        self.current_phone = phone
        log(f"🚀 Processing (reuse): {phone}")
        
        if not self.driver:
            log("No driver available for reuse!", "ERROR")
            return False
        
        try:
            # Navigate to start URL (browser already exists)
            self.driver.get('https://mbasic.facebook.com/login/identify/?ctx=recover')
            self.wait_for_ready(3)
            self.driver.execute_script("window.stop();")
            log("🛑 Force Stopped Home Page", "OK")

            # 2. Search - use DOM injection for speed
            inp = WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((By.NAME, "email")))
            self.driver.execute_script("arguments[0].value = arguments[1];", inp, phone)
            btn = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_for_ready(3)
            self.driver.execute_script("window.stop();")
            log("🛑 Force Stopped Post-Search", "OK")

            # 3. Handle intermediate pages ("Try another way")
            keywords = ["try another", "another way", "طريقة أخرى"]
            for _ in range(3):
                page_src = self.driver.page_source.lower()
                found = False
                for kw in keywords:
                    if kw in page_src:
                        try:
                            btns = self.driver.find_elements(By.CSS_SELECTOR, "a, button")
                            for btn in btns:
                                if kw.split()[0] in btn.text.lower():
                                    btn.click()
                                    time.sleep(1.5)
                                    self.driver.execute_script("window.stop();")
                                    log(f"Clicked: {kw}", "OK")
                                    found = True
                                    break
                        except: continue
                    if found: break
                if not found: break

            # 4. Selection
            self.driver.execute_script("window.stop();")
            self._save_step_screenshot("3_selection")
            
            sms_found = False
            # Check Radios
            radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            for r in radios:
                try:
                    parent = r.find_element(By.XPATH, "./..")
                    txt = parent.text.lower()
                    if any(k in txt for k in ["sms", "text", "رسالة", "phone"]):
                        self.driver.execute_script("arguments[0].click();", r)
                        sms_found = True
                        log("SMS radio selected", "OK")
                        break
                except: pass
            
            if not sms_found: # Fallback text click
                clickable = self.driver.find_elements(By.CSS_SELECTOR, "div[role='button'], span, label")
                for el in clickable:
                    if any(k in el.text.lower() for k in ["text message", "sms", "رسالة نصية"]):
                        el.click()
                        sms_found = True
                        log("SMS text selected", "OK")
                        break
            
            if not sms_found:
                log("❌ SMS Option NOT FOUND", "ERROR")
                return False

            # Submit Selection
            time.sleep(1)
            btns = self.driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            for b in btns:
                try:
                    self.driver.execute_script("arguments[0].click();", b)
                    log("Clicked submit", "OK")
                    break
                except: continue
            
            time.sleep(2)
            self.driver.execute_script("window.stop();")

            # 5. Verify Success
            current_url = self.driver.current_url
            if "recover/code" in current_url or "enter code" in self.driver.page_source.lower():
                log("🎉 SUCCESS: OTP SENT!", "SUCCESS")
                log(f"📱 URL: {current_url}")
                self._save_step_screenshot("success")
                return True
            else:
                log("Failed to verify OTP sent", "ERROR")
                self._save_step_screenshot("fail_verify")
                return False

        except Exception as e:
            log(f"Flow Reuse Error: {e}", "ERROR")
            # Don't quit driver - let main_worker decide
            return False

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if not target: return
    
    numbers = []
    if os.path.isfile(target):
        with open(target, 'r') as f: numbers = [re.sub(r'[^\d+]', '', line).strip() for line in f if line.strip()]
    else: numbers = [re.sub(r'[^\d+]', '', target).strip()]
    
    for phone in numbers:
        FacebookOTPBrowser(headless=True).run_flow(phone)
        if len(numbers) > 1: time.sleep(2)

if __name__ == "__main__":
    main()
