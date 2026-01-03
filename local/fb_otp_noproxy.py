"""
Facebook OTP Local Automation (NO PROXY - Local Testing)
=========================================================
Uses Selenium automation WITHOUT proxy.
For local testing only.

Designed for: Windows Local Testing
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

try:
    import requests
    import io
    # Use regular selenium (NO PROXY)
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    print("[DEBUG] Essential libraries imported successfully (NO PROXY MODE).", flush=True)
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}", flush=True)
    print("Please run: pip install selenium", flush=True)
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

class FacebookOTPBrowserLocal:
    # NO PROXY - Local Testing Mode
    USE_PROXY = False
    
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.wait_time = 15
        self.current_phone = None
        self.telegram_token = os.environ.get("TELEGRAM_TOKEN")
        self.telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        self.cookie_handled = False

    def _setup_driver(self):
        log("Setting up Chrome browser (DATA SAVER MODE)...")
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        
        # Old mobile user agent (reduces data usage)
        old_mobile_ua = "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 5 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36"
        
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"user-agent={old_mobile_ua}")
        options.add_argument("--window-size=360,640")  # Mobile size
        options.add_argument("--disable-notifications")
        options.add_argument("--lang=en-US")
        
        # SSL bypass for Chrome (important for proxy)
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors=yes")
        
        # === DATA SAVING OPTIONS ===
        # Disable images
        options.add_argument("--blink-settings=imagesEnabled=false")
        
        # Disable JavaScript (optional - may break some sites)
        # options.add_argument("--disable-javascript")
        
        # Disable CSS loading
        options.add_argument("--disable-remote-fonts")
        
        # Disable extensions and plugins
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        
        # Disable GPU and hardware acceleration
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        
        # Disable cache (for testing)
        options.add_argument("--disk-cache-size=0")
        
        # Block third-party content
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-translate")
        options.add_argument("--disable-default-apps")
        
        # Experimental options
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Block images
            "profile.managed_default_content_settings.stylesheets": 2,  # Block CSS
            "profile.managed_default_content_settings.fonts": 2,  # Block fonts
            "profile.managed_default_content_settings.plugins": 2,  # Block plugins
        }
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # NO PROXY - Local Testing Mode
        log("NO PROXY MODE - Using local connection", "INFO")

        try:
            if ChromeDriverManager:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
            
            # Timeouts
            self.driver.set_page_load_timeout(60)
            self.driver.set_script_timeout(30)
            self.wait = WebDriverWait(self.driver, 20)
            
            # Inject anti-detect scripts
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
            })
            
            log("Chrome browser initialized successfully (NO PROXY)", "OK")
            
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
        log(f"Starting OTP flow for {phone} (DATA SAVER MODE)")
        
        if not self._setup_driver():
            return False

        try:
            # 1. Open mbasic Facebook (lightest version - minimal data usage)
            # mbasic.facebook.com uses ~10x less data than www.facebook.com
            recovery_url = 'https://mbasic.facebook.com/login/identify/?ctx=recover'
            log(f"Opening: {recovery_url}", "INFO")
            self.driver.get(recovery_url)
            time.sleep(3)

            # 2. Enter Phone
            try:
                # Save screenshot: Step 1 - Page opened
                self._save_step_screenshot("1_page_opened")
                
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
                
                # Save screenshot: Step 2 - Phone entered
                self._save_step_screenshot("2_phone_entered")
                
                # Find and click submit button
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                    submit_btn.click()
                except:
                    inp.send_keys(Keys.ENTER)
                
                # Wait for page to load after search
                time.sleep(5)
                
                # Save screenshot: Step 3 - After search
                self._save_step_screenshot("3_after_search")
                
                log("Search completed, processing results...", "INFO")
                
            except Exception as e:
                self._save_step_screenshot("error_phone_entry")
                log(f"Could not find phone input field: {e}", "ERROR")
                return False

            # 3. Handle Results
            time.sleep(2)  # Extra wait for page stability
            url = self.driver.current_url
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            log(f"Current URL: {url}", "INFO")
            
            # Save screenshot: Step 4 - Results page
            self._save_step_screenshot("4_results_page")

            if "no search results" in page_text or "لم يتم العثور" in page_text:
                self._save_step_screenshot("not_found")
                log("Account not found for this number", "WARN")
                return False

            if "recover" not in url and "reset" not in url:
                # Try clicking "Try another way" if visible
                try:
                    btn = self.driver.find_element(By.LINK_TEXT, "Try another way")
                    btn.click()
                    time.sleep(3)
                except:
                    log("Continuing with current page...", "INFO")

            # 4. Select SMS and Send
            time.sleep(2)  # Wait for page to fully load
            try:
                page_source = self.driver.page_source.lower()
                log(f"Looking for SMS option on recovery page...", "INFO")
                
                # Save screenshot for debugging
                self.driver.save_screenshot("debug_recovery_page.png")
                log("Debug screenshot saved: debug_recovery_page.png", "INFO")
                
                # Method 1: Find SMS radio buttons
                radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                log(f"Found {len(radios)} radio buttons", "INFO")
                
                sms_found = False
                for r in radios:
                    outer_html = r.get_attribute("outerHTML").lower()
                    parent_text = ""
                    try:
                        parent = r.find_element(By.XPATH, "./..")
                        parent_text = parent.text.lower()
                    except:
                        pass
                    
                    if "sms" in outer_html or "sms" in parent_text or "text" in parent_text:
                        self.driver.execute_script("arguments[0].click();", r)
                        sms_found = True
                        log("SMS option found via radio button!", "OK")
                        break
                
                # Method 2: Look for clickable elements with SMS/text message text
                if not sms_found:
                    sms_keywords = ["send me a text", "text message", "sms", "رسالة نصية"]
                    clickable = self.driver.find_elements(By.CSS_SELECTOR, "div[role='button'], span, label")
                    for el in clickable:
                        el_text = el.text.lower()
                        for kw in sms_keywords:
                            if kw in el_text:
                                el.click()
                                sms_found = True
                                log(f"SMS option found via text match: '{kw}'", "OK")
                                break
                        if sms_found:
                            break
                
                # Method 3: Click continue/send button directly if SMS is default
                if not sms_found:
                    log("Attempting to click Continue button directly...", "INFO")
                
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
                            time.sleep(5)
                            break
                except:
                    # Fallback: try by name
                    try:
                        btn = self.driver.find_element(By.NAME, "reset_action")
                        btn.click()
                        log("Clicked reset_action button", "OK")
                        time.sleep(5)
                    except:
                        pass
                
                # 5. Verify Success
                current_url = self.driver.current_url
                page_text = self.driver.page_source.lower()
                
                if "recover/code" in current_url or "enter code" in page_text or "enter the code" in page_text:
                    log("🎉 SUCCESS: OTP SENT!", "SUCCESS")
                    screenshot_path = f"success_{phone}.png"
                    self.driver.save_screenshot(screenshot_path)
                    self.send_telegram_photo(f"✅ OTP SENT!\nPhone: {phone}\nStatus: Success", screenshot_path)
                    try:
                        os.remove(screenshot_path)
                    except:
                        pass
                    return True
                else:
                    log(f"Current URL after button click: {current_url}", "INFO")
                    log("Could not verify OTP sent status", "WARN")
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
    log("NO PROXY MODE - Local Testing", "OK")
    
    for phone in numbers:
        log(f"\n{'='*40}")
        log(f" PROCESSING: {phone}")
        log(f"{'='*40}")

        try:
            # Run OTP flow with proxy
            bot = FacebookOTPBrowserLocal(headless=headless)
            bot.run_flow(phone)
        except Exception as e:
            log(f"Error processing {phone}: {e}", "ERROR")
        
        # Small delay between numbers
        if len(numbers) > 1:
            log("Waiting 3 seconds before next number...")
            time.sleep(3)

if __name__ == "__main__":
    main()

