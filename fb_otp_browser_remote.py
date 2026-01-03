"""
Facebook OTP Browser Automation (Remote Browser API)
================================
Uses Selenium Remote WebDriver to connect to Bright Data Browser API
Opens remote browser, fills forms, clicks buttons

Designed by: Doctor Kayf (@Doc_kayf)
             https://t.me/Doc_kayf

Features:
- Real browser automation (bypasses anti-bot)
- Headless mode option
- Batch processing support
- Detailed logging

Requirements:
    pip install selenium webdriver-manager

Configuration:
    Set BRIGHTDATA_BROWSER_URL or BRIGHTDATA_BROWSER_USER/BRIGHTDATA_BROWSER_PASSWORD
    (host defaults to brd.superproxy.io, port defaults to 9515)

Usage:
    python fb_otp_browser_remote.py +201234567890
    python fb_otp_browser_remote.py numbers.txt
"""

import sys
import io
import os
import requests
import time
import re
import random
import threading
import tempfile
import urllib.parse
import zipfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


# Fix console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
SELENIUMWIRE_AVAILABLE = False

# Undetected Chromedriver removed by user request
UNDETECTED_AVAILABLE = False


# Colors (Disabled for Heroku compatibility)
class C:
    B = ''
    G = ''
    Y = ''
    R = ''
    CYAN = ''
    BOLD = ''
    END = ''

# Shared Statistics Class for Parallel Processing
class Stats:
    """Thread-safe statistics tracker"""
    def __init__(self, total):
        self.lock = threading.Lock()
        self.total = total
        self.processed = 0
        self.success = 0
        self.failed = 0
        self.not_found = 0
    
    def update(self, status):
        with self.lock:
            self.processed += 1
            if status == "OTP_SENT":
                self.success += 1
            elif status == "NOT_FOUND":
                self.not_found += 1
            else:
                self.failed += 1
    
    def display(self):
        """Display current statistics"""
        with self.lock:
            pct = (self.processed / self.total * 100) if self.total > 0 else 0
            print(f"\n{C.BOLD}{C.CYAN}╔══════════════════════════════════════════════════════════╗{C.END}")
            print(f"{C.BOLD}{C.CYAN}║{C.END}              📊 LIVE STATISTICS                          {C.BOLD}{C.CYAN}║{C.END}")
            print(f"{C.BOLD}{C.CYAN}╠══════════════════════════════════════════════════════════╣{C.END}")
            print(f"{C.BOLD}{C.CYAN}║{C.END}  📱 Total Numbers:     {self.total:<10}                     {C.BOLD}{C.CYAN}║{C.END}")
            print(f"{C.BOLD}{C.CYAN}║{C.END}  ⚡ Processed:         {self.processed:<10} ({pct:.1f}%)             {C.BOLD}{C.CYAN}║{C.END}")
            print(f"{C.BOLD}{C.CYAN}║{C.END}  {C.G}✓ Success (OTP Sent):{C.END} {self.success:<10}                     {C.BOLD}{C.CYAN}║{C.END}")
            print(f"{C.BOLD}{C.CYAN}║{C.END}  {C.Y}⚠ Not Found:{C.END}         {self.not_found:<10}                     {C.BOLD}{C.CYAN}║{C.END}")
            print(f"{C.BOLD}{C.CYAN}║{C.END}  {C.R}✗ Failed/Errors:{C.END}     {self.failed:<10}                     {C.BOLD}{C.CYAN}║{C.END}")
            print(f"{C.BOLD}{C.CYAN}╚══════════════════════════════════════════════════════════╝{C.END}\n")

def log(msg, level="INFO"):
    t = datetime.now().strftime("%H:%M:%S")
    colors = {"INFO": C.B, "OK": C.G, "WARN": C.Y, "ERROR": C.R, "SUCCESS": C.G + C.BOLD}
    c = colors.get(level, "")
    print(f"{C.CYAN}[{t}]{C.END} {c}[{level}] {msg}{C.END}", flush=True)


def _parse_proxy_url(proxy_url):
    if not proxy_url:
        return None
    raw = proxy_url.strip()
    if "://" not in raw:
        raw = f"http://{raw}"
    try:
        parsed = urllib.parse.urlparse(raw)
    except Exception:
        return None
    if not parsed.hostname or not parsed.port:
        return None
    username = urllib.parse.unquote(parsed.username) if parsed.username else None
    password = urllib.parse.unquote(parsed.password) if parsed.password else None
    return {
        "scheme": parsed.scheme or "http",
        "host": parsed.hostname,
        "port": str(parsed.port),
        "username": username,
        "password": password,
    }


def _get_proxy_config(default_proxy):
    proxy_url = os.environ.get("PROXY_URL") or os.environ.get("BRIGHTDATA_PROXY_URL")
    if proxy_url:
        parsed = _parse_proxy_url(proxy_url)
        if parsed:
            return parsed
        log("Invalid PROXY_URL format, falling back to defaults.", "WARN")
    return {
        "scheme": os.environ.get("PROXY_SCHEME") or os.environ.get("BRIGHTDATA_SCHEME") or "http",
        "host": os.environ.get("PROXY_HOST") or os.environ.get("BRIGHTDATA_HOST") or default_proxy["host"],
        "port": os.environ.get("PROXY_PORT") or os.environ.get("BRIGHTDATA_PORT") or str(default_proxy["port"]),
        "username": os.environ.get("PROXY_USERNAME") or os.environ.get("BRIGHTDATA_USERNAME") or default_proxy["username"],
        "password": os.environ.get("PROXY_PASSWORD") or os.environ.get("BRIGHTDATA_PASSWORD") or default_proxy["password"],
    }


def _resolve_proxy_ca_path():
    candidates = [
        os.environ.get("PROXY_CA_CERT"),
        os.environ.get("BRIGHTDATA_CA_CERT"),
        os.environ.get("BRIGHTDATA_CERT_PATH"),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    local_cert = os.path.join(os.path.dirname(__file__), "brightdata.crt")
    if os.path.exists(local_cert):
        return local_cert
    return None


def _resolve_verify_ssl():
    override = os.environ.get("PROXY_VERIFY_SSL")
    if not override:
        return None
    raw = override.strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    if os.path.exists(override):
        return True
    log("Invalid PROXY_VERIFY_SSL value, ignoring.", "WARN")
    return None


def _sanitize_sslkeylogfile():
    keylog = os.environ.get("SSLKEYLOGFILE")
    if not keylog:
        return None
    if keylog.startswith("\\\\.\\") or "nllMonFltProxy" in keylog:
        safe_path = os.path.join(tempfile.gettempdir(), "sslkeylog.log")
        os.environ["SSLKEYLOGFILE"] = safe_path
        log(f"SSLKEYLOGFILE redirected to {safe_path}", "WARN")
        return safe_path
    dir_name = os.path.dirname(keylog)
    if dir_name:
        try:
            os.makedirs(dir_name, exist_ok=True)
        except Exception:
            safe_path = os.path.join(tempfile.gettempdir(), "sslkeylog.log")
            os.environ["SSLKEYLOGFILE"] = safe_path
            log(f"SSLKEYLOGFILE redirected to {safe_path}", "WARN")
            return safe_path
    return keylog


def _mask_url(url):
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return "<invalid>"
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    return urllib.parse.urlunparse((parsed.scheme, host, parsed.path, "", "", ""))


def _get_remote_url():
    direct = (
        os.environ.get("BRIGHTDATA_BROWSER_URL")
        or os.environ.get("SELENIUM_REMOTE_URL")
        or os.environ.get("BROWSER_REMOTE_URL")
        or os.environ.get("BROWSER_API_URL")
    )
    if direct:
        return direct
    host = os.environ.get("BRIGHTDATA_BROWSER_HOST", "brd.superproxy.io")
    port = os.environ.get("BRIGHTDATA_BROWSER_PORT", "9515")
    user = os.environ.get("BRIGHTDATA_BROWSER_USER") or os.environ.get("BROWSER_API_USER")
    password = os.environ.get("BRIGHTDATA_BROWSER_PASSWORD") or os.environ.get("BROWSER_API_PASSWORD")
    if user and password:
        return f"https://{user}:{password}@{host}:{port}"
    return None


class ProxyManager:
    """Manages proxy rotation from a file"""
    
    def __init__(self, proxy_file=None):
        self.proxies = []
        self.current_index = 0
        self.lock = threading.Lock()
        
        if proxy_file:
            self.load_proxies(proxy_file)
    
    def load_proxies(self, filename):
        """Load proxies from file. Format: host:port:username:password"""
        try:
            with open(filename, 'r') as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split(':')
                        if len(parts) == 4:
                            self.proxies.append({
                                'host': parts[0],
                                'port': int(parts[1]),
                                'username': parts[2],
                                'password': parts[3]
                            })
            log(f"Loaded {len(self.proxies)} proxies from {filename}", "OK")
        except Exception as e:
            log(f"Failed to load proxies: {e}", "WARN")
    
    def get_next(self):
        """Get next proxy in rotation (thread-safe)"""
        if not self.proxies:
            return None
        with self.lock:
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            # Return string format for Selenium
            return f"{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
    
    def get_random(self):
        """Get a random proxy"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def parse_proxy(self, proxy_string):
        """Parse proxy string to components
        Format: host:port:username:password
        Returns dict with host, port, username, password
        """
        if not proxy_string:
            return None
        
        parts = proxy_string.split(':')
        if len(parts) >= 4:
            return {
                'host': parts[0],
                'port': parts[1],
                'username': parts[2],
                'password': ':'.join(parts[3:])  # Handle passwords with colons
            }
        elif len(parts) == 2:
            return {
                'host': parts[0],
                'port': parts[1],
                'username': None,
                'password': None
            }
        return None




class FacebookOTPBrowser:
    """Facebook OTP Automation using Selenium Browser"""
    
    # Bright Data Mobile Proxy Configuration (Zone 2)
    BRIGHTDATA_PROXY = {
        'host': 'brd.superproxy.io',
        'port': '33335',
        'username': 'brd-customer-hl_90769934-zone-mobile_proxy2',
        'password': 'ne17wi9deoiv'
    }
    
    def __init__(self, headless=True, use_brightdata=True):
        """
        Initialize Facebook OTP Browser
        
        Args:
            headless: Run in headless mode (default: True for Heroku)
            use_brightdata: Use Bright Data proxy (default: True)
        """
        self.driver = None
        self.headless = headless
        self.wait_time = 12
        self.use_brightdata = use_brightdata
        self.snapshot_taken = False
        self.wait = None
        self.current_phone = None
        self.cookie_handled = False
        
    def _create_proxy_auth_extension(self, proxy):
        """Create a Chrome extension for proxy authentication (Manifest V2 - Robust)"""
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy Auth V2",
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
                "scripts": ["background.js"],
                "persistent": true
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        chrome.webRequest.onAuthRequired.addListener(
            function(details) {
                return {
                    authCredentials: {
                        username: "%s",
                        password: "%s"
                    }
                };
            },
            {urls: ["<all_urls>"]},
            ["blocking"]
        );
        """ % (proxy['username'], proxy['password'])

        plugin_file = 'proxy_auth_plugin.zip'
        try:
            with zipfile.ZipFile(plugin_file, 'w') as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)
            log(f"Created proxy auth extension (V2): {plugin_file}", "INFO")
            return os.path.abspath(plugin_file)
        except Exception as e:
            log(f"Failed to create proxy extension: {e}", "ERROR")
            return None

    def _encode_proxy_auth(self, username, password):
        """Encode proxy credentials in Base64 for HTTP Basic Auth"""
        import base64
        credentials = f"{username}:{password}"
        return base64.b64encode(credentials.encode()).decode()


    def check_ip(self):
        """Check external IP to verify proxy with retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                log(f"Checking IP address via proxy (Attempt {attempt+1}/{max_retries})...", "INFO")
                # Use HTTP to avoid SSL overhead on this check
                self.driver.set_page_load_timeout(30)
                self.driver.get("http://api.ipify.org?format=json")
                # Restore timeout
                self.driver.set_page_load_timeout(180) 
                
                time.sleep(2)  # Wait for render
                content = self.driver.find_element(By.TAG_NAME, "body").text
                log(f"Current IP Info: {content}", "INFO")
                return True
            except Exception as e:
                log(f"IP Check failed (Attempt {attempt+1}): {e}", "WARN")
                time.sleep(3)
        
        return False


    # Note: send_telegram_photo is defined below at line 537


    def _save_failure_snapshot(self, step_name):
        """Save screenshot immediately"""
        if not self.driver: return
        try:
            timestamp = int(time.time())
            filename = f"fail_{step_name}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            log(f"Screenshot saved to: {filename}", "INFO")
            
            caption = f"⚠️ FAILURE: {step_name} [{self.current_phone}]\nURL: {self.driver.current_url}"
            self.send_telegram_photo(caption, filename)
        except Exception as e:
            log(f"Failed to save failure snapshot: {e}", "WARN")

    def _handle_failure(self, step_name):
        self._save_failure_snapshot(step_name)

    def _save_screenshot(self, name):
         """Helper to save normal flow screenshot"""
         try:
             timestamp = int(time.time())
             filename = f"{name}_{timestamp}.png"
             self.driver.save_screenshot(filename)
             caption = f"📸 Step: {name} [{self.current_phone}]"
             self.send_telegram_photo(caption, filename)
         except: pass

    def _setup_driver(self):
        """Setup Remote Chrome WebDriver via Bright Data Browser API"""
        print("DEBUG: Entering _setup_driver...", flush=True)
        log("Setting up Remote Chrome (Bright Data Browser API)...")
        _sanitize_sslkeylogfile()
        
        # Desktop User Agent
        desktop_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        
        # Chrome Options
        options = Options()
        
        if self.headless:
            options.add_argument("--headless=new")
            log("Running in HEADLESS=NEW mode", "INFO")
            
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"user-agent={desktop_ua}")
        options.add_argument("--window-size=1100,600")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-gpu")
        
        remote_url = _get_remote_url()
        if not remote_url:
            self._chrome_error = "Remote browser URL not configured"
            log("Missing BRIGHTDATA_BROWSER_URL or Browser API credentials.", "ERROR")
            return False

        masked_url = _mask_url(remote_url)
        log(f"Connecting to remote browser: {masked_url}", "INFO")

        try:
            self.driver = webdriver.Remote(command_executor=remote_url, options=options)
            self.driver.set_page_load_timeout(180)
            self.driver.set_script_timeout(120)
            self.wait = WebDriverWait(self.driver, 30)
            log("Remote WebDriver initialized successfully.", "SUCCESS")
            return True
        except Exception as e:
            self._chrome_error = str(e)
            log(f"Critical Error initializing Remote WebDriver: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            self._close_driver()
            return False

    
    def _close_driver(self):
        """Close the browser and cleanup temp files"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
        # Cleanup screenshot files
        self._cleanup_screenshots()
    
    def _cleanup_screenshots(self):
        """Delete temporary screenshot files after sending to Telegram"""
        try:
            import glob
            for f in glob.glob("*.png"):
                if f.startswith(("fail_", "snap_", "1_", "2_", "3_", "4_", "5_", "6_")):
                    try:
                        os.remove(f)
                    except:
                        pass
        except:
            pass
    
    def _wait_for_element(self, by, value, timeout=None):
        """Wait for element to be present"""
        timeout = timeout or self.wait_time
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def _wait_and_click(self, by, value, timeout=None):
        """Wait for element and click"""
        timeout = timeout or self.wait_time
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            return True
        except TimeoutException:
            return False
            
    def random_sleep(self, min_time, max_time):
        """Sleep for a random amount of time"""
        sleep_time = random.uniform(min_time, max_time)
        time.sleep(sleep_time)

    def send_telegram_photo(self, caption, file_path):
        """Send a photo to the configured Telegram chat."""
        token = os.environ.get("TELEGRAM_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        if not token or not chat_id:
            return

        try:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            
            # Retry logic for 429
            max_retries = 3
            for attempt in range(max_retries):
                with open(file_path, "rb") as f:
                    files = {"photo": f}
                    data = {"chat_id": chat_id, "caption": caption}
                    response = requests.post(url, files=files, data=data)
                    
                if response.status_code == 200:
                    self.snapshot_taken = True
                    log(f"Sent Telegram photo: {caption}", "OK")
                    return
                elif response.status_code == 429:
                    retry_after = 5 # Default
                    try:
                        resp_json = response.json()
                        retry_after = resp_json.get('parameters', {}).get('retry_after', 5)
                    except:
                        pass
                    log(f"Telegram Rate Limit (429). Waiting {retry_after}s...", "WARN")
                    time.sleep(retry_after + 1)
                    continue # Retry loop
                else:
                    log(f"Failed to send Telegram photo: {response.text}", "WARN")
                    break # Don't retry other errors
                    
        except Exception as e:
            log(f"Error sending Telegram photo: {e}", "WARN")


    def simulate_human_behavior(self):
        """Simulate human-like interactions with the page"""
        try:
            # Random small scroll
            scroll_amount = random.randint(50, 200)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.3, 0.8))
            
            # Sometimes scroll back up a bit
            if random.choice([True, False]):
                self.driver.execute_script(f"window.scrollBy(0, -{scroll_amount // 2});")
                time.sleep(random.uniform(0.2, 0.5))
            
            # Move mouse randomly (inject mouse move event)
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            self.driver.execute_script(f"""
                var event = new MouseEvent('mousemove', {{
                    'view': window,
                    'bubbles': true,
                    'cancelable': true,
                    'clientX': {x},
                    'clientY': {y}
                }});
                document.dispatchEvent(event);
            """)
            time.sleep(random.uniform(0.1, 0.3))
        except:
            pass

    # ==========================================
    # NEW DESKTOP OTP FLOW STEPS
    # ==========================================

    def _handle_cookie_consent(self):
        """Handle cookie consent popup if it appears - Uses JS to click inner span"""
        # Skip if already handled
        if self.cookie_handled:
            return True
        
        try:
            # PRIMARY METHOD: JavaScript click on span (TESTED & WORKING)
            js_click_cookie = """
            (function() {
                // Method 1: Click inner span directly (MOST RELIABLE)
                let spans = [...document.querySelectorAll('span')];
                let target = spans.find(s => s.innerText === 'Allow all cookies');
                if (target) { target.click(); return 'clicked_span_en'; }
                
                // Method 2: Arabic text
                target = spans.find(s => s.innerText.includes('السماح'));
                if (target) { target.click(); return 'clicked_span_ar'; }
                
                // Method 3: Fallback to aria-label div
                let btn = document.querySelector('div[aria-label="Allow all cookies"]');
                if (btn) { 
                    let innerSpan = btn.querySelector('span');
                    if (innerSpan) { innerSpan.click(); return 'clicked_inner_span'; }
                    btn.click(); 
                    return 'clicked_div'; 
                }
                
                // Method 4: data-testid
                btn = document.querySelector('[data-testid="cookie-policy-manage-dialog-accept-button"]');
                if (btn) { btn.click(); return 'clicked_testid'; }
                
                // Method 5: First button in any dialog
                let dialog = document.querySelector('div[role="dialog"]');
                if (dialog) {
                    let firstBtn = dialog.querySelector('button');
                    if (firstBtn) { firstBtn.click(); return 'clicked_dialog_btn'; }
                }
                
                return 'not_found';
            })();
            """
            
            result = self.driver.execute_script(js_click_cookie)
            
            if result and result != 'not_found':
                log(f"Cookie consent accepted ({result})!", "OK")
                self.cookie_handled = True  # Mark as handled
                time.sleep(0.5)  # Reduced from 1s
                return True
            
            return False
        except Exception as e:
            return False

    def step1_open_recovery_page(self, phone=""):
        """Step 1: Open Facebook Identify Page (Desktop) - With Retry"""
        step_name = "1_open_identify"
        log(f"Step 1: Opening Facebook Identify [{phone}]...")
        
        # Retry logic for network issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Increase page load timeout for slow VPN connections
                self.driver.set_page_load_timeout(90)
                
                self.driver.get('https://www.facebook.com/login/identify/?ctx=recover&from_login_screen=0')
                
                # Wait for page to actually load (check for input field OR body content)
                page_loaded = False
                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.ID, "identify_email"))
                    )
                    page_loaded = True
                    log(f"Page loaded successfully (attempt {attempt + 1})", "OK")
                except:
                    # Check if page has any content
                    try:
                        body = self.driver.find_element(By.TAG_NAME, "body")
                        if body and len(body.text) > 50:
                            page_loaded = True
                            log(f"Page loaded with content (attempt {attempt + 1})", "OK")
                    except:
                        pass
                
                if not page_loaded:
                    raise Exception("Page did not load properly - no content")
                
                time.sleep(0.5)  # Brief wait before cookie check
                
                # Check for cookie consent dialog
                self._handle_cookie_consent()
                
                # Send progress screenshot
                self._save_screenshot("step1_page_opened")
                return True
                
            except Exception as e:
                log(f"Attempt {attempt + 1}/{max_retries} failed: {e}", "WARN")
                if attempt < max_retries - 1:
                    wait_time = 3 * (attempt + 1)  # Exponential backoff: 3s, 6s
                    log(f"Retrying in {wait_time} seconds...", "INFO")
                    time.sleep(wait_time)
                    try:
                        self.driver.refresh()
                    except:
                        pass
                else:
                    self._handle_failure(step_name)
                    return False
        
        return False

    def step2_enter_phone(self, number):
        """Step 2: Enter number (Desktop Flow) - With Retry"""
        step_name = "2_enter_phone"
        log(f"Step 2: Entering phone [{number}]...")
        # Check cookies again (sometimes appears late)
        self._handle_cookie_consent()
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Try multiple selectors for input field with longer timeout
                input_selectors = [
                    (By.ID, "identify_email"),
                    (By.NAME, "email"),
                    (By.CSS_SELECTOR, "input[name='email']"),
                    (By.CSS_SELECTOR, "input[type='text']"),
                    (By.CSS_SELECTOR, "input[type='tel']"),
                    (By.XPATH, "//input[@placeholder]"),
                    (By.XPATH, "//form//input"),
                ]
                
                inp = None
                for by, selector in input_selectors:
                    try:
                        inp = WebDriverWait(self.driver, 30).until(
                            EC.presence_of_element_located((by, selector))
                        )
                        if inp and inp.is_displayed():
                            log(f"Found input field: {selector}", "INFO")
                            break
                    except:
                        continue
                
                # JavaScript fallback if Selenium didn't find it
                if not inp:
                    try:
                        js_result = self.driver.execute_script("""
                            var inp = document.getElementById('identify_email') || 
                                      document.querySelector('input[name="email"]') ||
                                      document.querySelector('input[type="text"]');
                            if (inp) { return 'found'; }
                            return 'not_found';
                        """)
                        if js_result == 'found':
                            inp = self.driver.find_element(By.CSS_SELECTOR, "input")
                            log("Found input field via JavaScript", "INFO")
                    except:
                        pass
                
                if not inp:
                    if attempt < max_retries - 1:
                        log(f"Input not found (attempt {attempt + 1}), refreshing...", "WARN")
                        self.driver.refresh()
                        time.sleep(1.5)
                        continue
                    log("Could not find input field", "ERROR")
                    self._handle_failure(step_name)
                    return False
                
                inp.clear()
                inp.send_keys(number)
                
                # Send progress screenshot
                self._save_screenshot("step2_phone_entered")
                return True
                
            except Exception as e:
                if attempt < max_retries - 1:
                    log(f"Step 2 attempt {attempt + 1} failed: {e}", "WARN")
                    time.sleep(1)
                    continue
                self._handle_failure(step_name)
                return False
        
        return False

    def step3_click_search(self, phone=""):
        """Step 3: Click Search using ENTER key"""
        step_name = "3_click_search"
        log(f"Step 3: Submitting Search [{phone}]...")
        # Check cookies crucial here
        self._handle_cookie_consent()
        try:
            # Get current URL before clicking
            url_before = self.driver.current_url
            
            # 1. Locate the input field again (safest approach)
            log("Locating input field to press ENTER...", "INFO")
            inp = None
            try:
                inp = self.driver.find_element(By.ID, "identify_email")
            except:
                try:
                    inp = self.driver.find_element(By.NAME, "email")
                except:
                    pass
            
            if inp:
                log("Input field found. Sending ENTER key...", "INFO")
                inp.send_keys(Keys.ENTER)
                log("Sent ENTER key!", "OK")
            else:
                # Fallback: Try JS Click on button if input is somehow gone
                log("Input field not found! Trying fallback JS click on button...", "WARN")
                self.driver.execute_script("document.getElementById('did_submit').click();")
            
            # Wait longer for page to load through proxy
            time.sleep(5)
            
            # Check if page changed
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: "This is my account" in d.page_source or 
                              "هذا هو حسابي" in d.page_source or
                              "Reset your password" in d.page_source or
                              "Identify your account" in d.page_source or
                              "These accounts matched" in d.page_source or
                              d.current_url != url_before
                )
                log("Page content changed after Search - navigation successful!", "OK")
            except:
                log("Page may not have changed, verifying content...", "WARN")
            
            # Send progress screenshot
            self._save_screenshot("step3_search_clicked")
            return True
        except Exception as e:
            log(f"Search submission failed: {e}", "ERROR")
            self._handle_failure(step_name)
            return False

    def step4_check_account_found(self, phone=""):
        """Step 4: Analyze Search Result"""
        step_name = "4_check_result"
        log(f"Step 4: Checking account result [{phone}]...")
        time.sleep(1)  # Wait 1 second before checking result
        try:
            url = self.driver.current_url
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            # Case 1: No Result - CHECK FIRST before anything else
            not_found_patterns = [
                "no result", "no search results", "didn't match", 
                "لم يتم العثور", "لا توجد نتائج", "try again with other"
            ]
            for pattern in not_found_patterns:
                if pattern in page_text:
                    log(f"NOT_FOUND detected: '{pattern}'", "WARN")
                    return "NOT_FOUND"
            
            # Case 1.5: "Log Into Facebook" Password Screen (intermediate step)
            # User reported this screen appears instead of recovery options.
            # We need to treat this like "TRY_ANOTHER_WAY" to force a redirect.
            if "log into facebook" in page_text or "تسجيل الدخول" in page_text:
                 # Check if password field is present to confirm it's the login screen
                 if "pass" in page_text or self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']"):
                      log("Detected 'Log Into Facebook' password screen. Redirecting...", "INFO")
                      return "TRY_ANOTHER_WAY"

            # Case 2: Multiple Accounts - Auto-select first account using JS
            if "this is my account" in page_text or "هذا حسابي" in page_text:
                log("Multiple accounts found - selecting first one...", "INFO")
                js_select_first = """
                (function() {
                    let btns = [...document.querySelectorAll('a, button, div[role="button"]')];
                    let target = btns.find(b => b.innerText.includes('This is my account') || b.innerText.includes('هذا حسابي'));
                    if (target) { target.click(); return 'selected'; }
                    return 'not_found';
                })();
                """
                result = self.driver.execute_script(js_select_first)
                if result == 'selected':
                    log("First account selected!", "OK")
                    time.sleep(1)
                return "MULTIPLE_ACCOUNTS"
            
            # Case 3: Still on identify page (but with ctx=recover = need to click "Try another way")
            if "identify" in url:
                if "ctx=recover" in url:
                    log("Detected identify page with ctx=recover - treating as TRY_ANOTHER_WAY", "INFO")
                    return "TRY_ANOTHER_WAY"
                else:
                    return "NOT_FOUND"
                
            # Case 4: Recover Page (Direct success)
            if "recover" in url or "reset" in url:
                return "FOUND"

            # Fallback
            return "UNKNOWN"

        except Exception as e:
            return "ERROR"

    def _check_broken_page(self):
        """Check for 'This page isn't available' error and reload"""
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            broken_indicators = [
                "page isn't available", 
                "broken link",
                "reload page",
                "هذه الصفحة غير متوفرة",
                "إعادة تحميل الصفحة"
            ]
            
            if any(ind in page_text for ind in broken_indicators):
                log("⚠️ Broken/Error page detected! Reloading...", "WARN")
                self.driver.refresh()
                time.sleep(4)
                return True
            return False
        except:
            return False

    def step5_select_sms_option(self, number):
        """Step 5: Select SMS Option"""
        step_name = "5_select_sms"
        log(f"Step 5: Selecting SMS option [{number}]...")
        try:
            # Force Navigate if not already on recovery page
            if "recover" not in self.driver.current_url:
                 self.driver.get("https://www.facebook.com/recover/initiate/?is_from_lara_screen=1")
                 time.sleep(3)
            
            # Check for specific "Page isn't available" error
            self._check_broken_page()
            
            # CRITICAL FIX: Check for "Try another way" (Intermediate Screen)
            # If we see this, we must click it to reveal the actual radio options
            try:
                try_another = None
                try_texts = ["try another way", "جرب طريقة أخرى", "طريقة أخرى"]
                
                # Check buttons and links
                candidates = self.driver.find_elements(By.XPATH, "//a | //button | //div[@role='button']")
                for el in candidates:
                    if any(t in el.text.lower() for t in try_texts):
                         try_another = el
                         break
                
                if try_another and try_another.is_displayed():
                    log(f"Found 'Try another way' button. Clicking to reveal options...", "INFO")
                    self.driver.execute_script("arguments[0].click();", try_another)
                    time.sleep(0.8) # Wait for options to load
            except Exception as e:
                log(f"Check for 'Try another way' failed (non-critical): {e}", "WARN")

            # STEP A: Click on SMS option (Using exact selector from browser success test)
            # IMPORTANT: This click is required to prevent redirect loops, even if pre-selected.
            log("Clicking SMS option (Required)...", "INFO")
            sms_clicked = False
            
            # Method 1: Exact ID selector that worked in browser test
            try:
                sms_radio = self.driver.find_element(By.CSS_SELECTOR, "input[id^='send_sms']")
                self.driver.execute_script("arguments[0].click();", sms_radio)
                log("Clicked SMS radio (id^=send_sms)!", "OK")
                sms_clicked = True
            except:
                pass
            
            # Method 2: Find label with 'sms' text
            if not sms_clicked:
                try:
                    labels = self.driver.find_elements(By.TAG_NAME, "label")
                    for l in labels:
                        if "sms" in l.text.lower():
                            self.driver.execute_script("arguments[0].click();", l)
                            log(f"Clicked SMS label: {l.text[:30]}", "OK")
                            sms_clicked = True
                            break
                except:
                    pass
            
            # Method 3: Any radio button with SMS context
            if not sms_clicked:
                try:
                    radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                    for r in radios:
                        if "sms" in r.get_attribute("outerHTML").lower():
                            self.driver.execute_script("arguments[0].click();", r)
                            log("Clicked generic SMS radio button", "OK")
                            sms_clicked = True
                            break
                except:
                    pass
            
            if not sms_clicked:
                log("No SMS option found - proceeding anyway", "WARN")
            
            time.sleep(0.5) # Wait for selection to register
            
            # ---------------------------------------------------------
            # CONTINUE BUTTON CLICK - With Fallback Methods
            # Primary: name="reset_action", Fallback: type="submit" or text match
            # ---------------------------------------------------------
            log("Clicking 'Continue' button...", "INFO")
            
            continue_clicked = False
            
            # Method 1: JavaScript - Try multiple selectors
            try:
                js_result = self.driver.execute_script("""
                    // Method A: name=reset_action (PRIMARY)
                    var btn = document.querySelector('button[name="reset_action"]');
                    if (btn) { btn.click(); return 'reset_action'; }
                    
                    // Method B: type=submit (skip "Not you" buttons)
                    var btns = document.querySelectorAll('button[type="submit"]');
                    for (var b of btns) {
                        var txt = b.innerText.toLowerCase();
                        if (!txt.includes('not') && !txt.includes('ليس')) {
                            b.click();
                            return 'submit_btn';
                        }
                    }
                    
                    // Method C: Any button with Continue/متابعة text
                    btns = document.querySelectorAll('button');
                    for (var b of btns) {
                        var txt = b.innerText.toLowerCase();
                        if (txt.includes('continue') || txt.includes('متابعة')) {
                            if (!txt.includes('not') && !txt.includes('ليس')) {
                                b.click();
                                return 'continue_text';
                            }
                        }
                    }
                    
                    return 'not_found';
                """)
                
                if js_result and js_result != 'not_found':
                    log(f"Clicked Continue button (JS: {js_result})!", "OK")
                    continue_clicked = True
            except Exception as e:
                log(f"JS Continue click failed: {e}", "WARN")
            
            # Method 2: Selenium fallback
            if not continue_clicked:
                try:
                    # Try name=reset_action
                    btn = self.driver.find_element(By.NAME, "reset_action")
                    if btn.is_displayed():
                        btn.click()
                        log("Clicked Continue button (Selenium: name=reset_action)!", "OK")
                        continue_clicked = True
                except:
                    pass
            
            # Method 3: Any submit button
            if not continue_clicked:
                try:
                    btns = self.driver.find_elements(By.CSS_SELECTOR, "button[type='submit']")
                    for b in btns:
                        txt = b.text.lower()
                        if "not" not in txt and "ليس" not in txt:
                            b.click()
                            log("Clicked Continue button (Selenium: submit)!", "OK")
                            continue_clicked = True
                            break
                except:
                    pass
            
            if not continue_clicked:
                log("❌ Continue button NOT clicked!", "ERROR")
                return False, "CONTINUE_BTN_MISSING"

            time.sleep(1.0) # Wait for processing
            self._save_screenshot(step_name + "_success")
            return True, "OK"

        except Exception as e:
            self._handle_failure(step_name)
            return False, str(e)

    def step6_send_code(self):
        """Step 6: Verify Success"""
        step_name = "6_verify_send"
        try:
            url = self.driver.current_url
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            self._save_screenshot(step_name)
            
            # Success indicators
            success_keywords = [
                "enter code", "أدخل الرمز", 
                "we sent", "تم الإرسال", 
                "check your phone", 
                "confirm your account"
            ]
            
            is_success = False
            if "recover/code" in url or "recover/password" in url or "enter_code" in url:
                is_success = True
            else:
                for kw in success_keywords:
                    if kw in page_text:
                        is_success = True
                        break
            
            if is_success:
                 log(f"🎉 OTP SUCCESS! Page: {url}", "SUCCESS")
                 return True, "SENT"
            else:
                 log(f"⚠️ Unsure of success. URL: {url}", "WARN")
                 # Check for captcha
                 if "security check" in page_text or "enter the text" in page_text or "captcha" in page_text:
                     return False, "CAPTCHA"
                 return True, "SENT_BUT_UNVERIFIED" # Still count as success if no clear error
                 
        except Exception as e:
            return False, str(e)

    
    def send_otp(self, phone):
        """Main function: Send OTP to phone - Desktop Flow"""
        self.current_phone = phone
        original_phone = phone
        phone = format_phone(phone)
        
        print(f"\n{'='*60}")
        print(f"{C.BOLD}{C.CYAN}   Facebook OTP (Desktop) - {phone}{C.END}")
        print("="*60)
        
        result = {"phone": phone, "status": "ERROR", "message": "Unknown error", "last_url": ""}
        
        try:
            # Setup browser
            if not self._setup_driver():
                error_detail = getattr(self, '_chrome_error', 'Unknown error')
                result["message"] = f"Failed to setup browser: {error_detail}"
                return result
            
            # Verify Proxy/IP
            self.check_ip()
            
            # LOOP for Multiple Accounts (Default 1 pass - NO RETRY)

            # User Request: Disable loop on failure.
            max_accounts_to_process = 1 
            accounts_processed = 0
            
            # Only loop if we explicitly detect multiple accounts later
            while accounts_processed < max_accounts_to_process:
                
                # If this is the 2nd+ iteration, we need to restart the flow to get a clean state
                if accounts_processed > 0:
                    log(f"--- Processing Account #{accounts_processed + 1} ---", "INFO")
                    time.sleep(2)
                
                # ========== STEP 1: Open identify page ==========
                if not self.step1_open_recovery_page(phone):
                    result["message"] = "Failed to open recovery page"
                    break # Critical failure
                
                # ========== STEP 2: Enter phone ==========
                if not self.step2_enter_phone(phone):
                    result["message"] = "Failed to enter phone"
                    break
                
                # ========== STEP 3: Search ==========
                if not self.step3_click_search(phone):
                    result["message"] = "Failed to click search"
                    break
                    
                # ========== STEP 4: Check Result ==========
                status = self.step4_check_account_found(phone)
                self._save_screenshot(f"4_Result_{status}")
                
                if status == "NOT_FOUND":
                    log("Account NOT FOUND (Final)", "WARN")
                    result["status"] = "NOT_FOUND"
                    break
                
                elif status == "TRY_ANOTHER_WAY":
                    log("Redirected to Login - Clicking 'Try Another Way'...", "INFO")
                    try:
                        # Navigate to the recovery initiate page
                        self.driver.get("https://www.facebook.com/recover/initiate/?is_from_lara_screen=1")
                        time.sleep(1.5)
                        
                        # RE-ENTER THE PHONE NUMBER on this page
                        try:
                            inp = self.driver.find_element(By.ID, "identify_email")
                            inp.clear()
                            inp.send_keys(phone)
                            log(f"Re-entered phone on recovery page: {phone}", "OK")
                            time.sleep(1)
                            
                            # Click Continue/Search on this page
                            try:
                                btn = self.driver.find_element(By.ID, "did_submit")
                                btn.click()
                            except:
                                btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                                btn.click()
                            log("Clicked search on recovery page", "OK")
                            time.sleep(1.5)
                        except Exception as e:
                            log(f"Could not re-enter phone: {e}", "WARN")
                        
                        # Verify we are now on proper recovery page
                        if "recover" in self.driver.current_url or "reset" in self.driver.current_url:
                             status = "FOUND" # Proceed to next steps
                        else:
                             log("Failed to navigate to recovery after redirect", "ERROR")
                             break
                    except Exception as e:
                        log(f"Error processing Try Another Way: {e}", "ERROR")
                        break
                        
                elif status == "MULTIPLE_ACCOUNTS":
                    log("Multiple accounts detected!", "INFO")
                    try:
                        # Find all "This is me" buttons
                        buttons = self.driver.find_elements(By.XPATH, "//a[@role='button']")
                        
                        valid_buttons = []
                        for b in buttons:
                             if "account" in b.text.lower() or "هذا إيميل" in b.text or "حسابي" in b.text:
                                 valid_buttons.append(b)
                        
                        num_accounts = len(valid_buttons)
                        log(f"Found {num_accounts} valid account buttons.", "INFO")
                        
                        # Only now do we increase the loop limit
                        max_accounts_to_process = num_accounts
                        
                        if accounts_processed >= num_accounts:
                            log("All accounts processed.", "OK")
                            break
                            
                        # Click the button for the current index
                        try:
                            target_btn = valid_buttons[accounts_processed]
                            log(f"Selecting account #{accounts_processed + 1}...", "INFO")
                            target_btn.click()
                            time.sleep(3)
                            
                            # Force navigate to recovery initiate just in case
                            self.driver.get("https://www.facebook.com/recover/initiate/?is_from_lara_screen=1")
                            time.sleep(3)
                            
                        except Exception as e:
                            log(f"Error identifying account button: {e}", "ERROR")
                            break
                            
                    except Exception as e:
                        log(f"Error handling multiple accounts: {e}", "ERROR")
                        break
                elif status == "FOUND":
                    log("Account FOUND - proceeding to SMS selection...", "OK")
                    # Continue to Step 5 (no break)
                    pass
                else:
                    log(f"Unknown status: {status}", "WARN")
                    break # Unknown status


                # ========== STEP 5: Select SMS ==========
                success, reason = self.step5_select_sms_option(phone)
                if not success:
                    log(f"Failed to select SMS: {reason}", "WARN")
                    accounts_processed += 1
                    continue # Try next account if any

                # ========== STEP 6: Verify Sent ==========
                success_6, reason_6 = self.step6_send_code()
                if success_6:
                    result["status"] = "OTP_SENT"
                    result["message"] = f"OTP Sent to account #{accounts_processed + 1}"
                    result["otp_url"] = self.driver.current_url
                    result["last_url"] = self.driver.current_url
                    
                    # Send success snapshot
                    otp_caption = f"✅ OTP SENT | {phone}\n🔗 OTP URL:\n{result['otp_url']}"
                    try:
                        timestamp = int(time.time())
                        filename = f"snap_6_SendSuccess_{timestamp}.png"
                        self.driver.save_screenshot(filename)
                        self.send_telegram_photo(otp_caption, filename)
                    except: pass
                    
                    break # SUCCESS! Stop looking
                else:
                    log(f"Failed to verify send: {reason_6}", "WARN")
                
                accounts_processed += 1
                
            # END LOOP
            
        except Exception as e:
            log(f"CRITICAL ERROR: {e}", "ERROR")
            result["message"] = str(e)
            
        finally:
            self._close_driver()
            
        return result



# ==========================================
# Batch Processing Logic
# ==========================================

def format_phone(phone):
    """Clean phone number"""
    return re.sub(r'[^\d+]', '', phone).strip()

def process_batch(numbers, headless=True, max_workers=1):
    """Process a list of numbers"""
    stats = Stats(len(numbers))
    results = []
    
    print(f"\n{C.B}Starting batch process for {len(numbers)} numbers...{C.END}")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_phone = {
            executor.submit(FacebookOTPBrowser(headless=headless).send_otp, phone): phone 
            for phone in numbers
        }
        
        for future in as_completed(future_to_phone):
            phone = future_to_phone[future]
            try:
                res = future.result()
                stats.update(res["status"])
                stats.display()
                results.append(res)
            except Exception as exc:
                print(f'{phone} generated an exception: {exc}')
                print(f"FINAL_STATUS_MSG: {str(exc)}")
                stats.update("ERROR")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    arg = sys.argv[1]
    
    # Check if arg is a file
    if os.path.isfile(arg):
        with open(arg, 'r') as f:
            numbers = [line.strip() for line in f if line.strip()]
        if not numbers:
            print("File is empty!")
            sys.exit(1)
        process_batch(numbers, headless=True, max_workers=1)
    else:
        # Single number
        browser = FacebookOTPBrowser(headless=True) # Ensure headless for batch
        try:
             res = browser.send_otp(arg)
             # Always print last URL
             last_url = res.get('last_url', res.get('otp_url', ''))
             if last_url:
                 print(f"Last URL: {last_url}")
             
             # Print final status for shell script extraction
             if res['status'] == 'ERROR':
                 print(f"FINAL_STATUS_MSG: {res['message']}")
             elif res['status'] == 'OTP_SENT':
                  print("OTP_SENT") 
             elif res['status'] == 'NOT_FOUND':
                  print("FINAL_STATUS_MSG: Account Not Found")
             else:
                  print(f"FINAL_STATUS_MSG: {res.get('message', 'Unknown')}")
        except Exception as e:
             print(f"FINAL_STATUS_MSG: Critical Script Error: {e}")

