"""
Facebook OTP Browser Automation - Scraping Browser Edition
===========================================================
Uses BrightData's Scraping Browser API (Remote Browser)
Instead of running local Chrome, connects to BrightData's hosted browser.

Selenium URL: https://{username}:{password}@brd.superproxy.io:9515

Usage:
    python fb_otp_scraping_browser.py +201234567890
"""

import sys
import io
import os
import time
import random
from datetime import datetime

# Fix console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

# ==========================================
# COLORS
# ==========================================
class C:
    R = "\033[91m"
    G = "\033[92m"
    Y = "\033[93m"
    B = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"

def log(msg, level="INFO"):
    t = datetime.now().strftime("%H:%M:%S")
    colors = {"INFO": C.B, "OK": C.G, "WARN": C.Y, "ERROR": C.R, "SUCCESS": C.G + C.BOLD}
    c = colors.get(level, "")
    print(f"{C.CYAN}[{t}]{C.END} {c}[{level}] {msg}{C.END}", flush=True)

# ==========================================
# BRIGHTDATA SCRAPING BROWSER CONFIG
# ==========================================
SCRAPING_BROWSER = {
    'username': 'brd-customer-hl_90769934-zone-scraping_browser1',
    'password': 'ap15sb7mo3rd',
    'host': 'brd.superproxy.io',
    'port': 9515  # Selenium port
}

class FacebookOTPScrapingBrowser:
    """Facebook OTP automation using BrightData Scraping Browser (Remote)"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.wait_time = 30
        self.cookie_handled = False
        
    def _setup_driver(self):
        """Connect to BrightData's Remote Scraping Browser"""
        log("Connecting to BrightData Scraping Browser...", "INFO")
        
        try:
            # Build Selenium Remote URL
            auth = f"{SCRAPING_BROWSER['username']}:{SCRAPING_BROWSER['password']}"
            remote_url = f"https://{auth}@{SCRAPING_BROWSER['host']}:{SCRAPING_BROWSER['port']}"
            
            log(f"Remote URL: {SCRAPING_BROWSER['host']}:{SCRAPING_BROWSER['port']}", "INFO")
            
            # Chrome options for remote browser
            options = Options()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--window-size=1280,720")
            
            # Connect to remote browser
            self.driver = webdriver.Remote(
                command_executor=remote_url,
                options=options
            )
            
            log("Connected to Scraping Browser!", "SUCCESS")
            
            # Set timeouts
            self.driver.set_page_load_timeout(120)
            self.driver.set_script_timeout(60)
            self.wait = WebDriverWait(self.driver, self.wait_time)
            
            return True
            
        except Exception as e:
            log(f"Failed to connect to Scraping Browser: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
    
    def _close_driver(self):
        """Close remote browser session"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def check_ip(self):
        """Verify we're using the remote browser"""
        try:
            log("Checking IP via Scraping Browser...", "INFO")
            self.driver.get("http://api.ipify.org?format=json")
            time.sleep(2)
            content = self.driver.find_element(By.TAG_NAME, "body").text
            log(f"Remote Browser IP: {content}", "OK")
            return True
        except Exception as e:
            log(f"IP Check failed: {e}", "WARN")
            return False
    
    def _handle_cookie_consent(self):
        """Handle cookie consent popup"""
        if self.cookie_handled:
            return True
        
        try:
            js_click_cookie = """
            (function() {
                let spans = [...document.querySelectorAll('span')];
                let target = spans.find(s => s.innerText === 'Allow all cookies');
                if (target) { target.click(); return 'clicked_en'; }
                
                target = spans.find(s => s.innerText.includes('السماح'));
                if (target) { target.click(); return 'clicked_ar'; }
                
                let btn = document.querySelector('div[aria-label="Allow all cookies"]');
                if (btn) { btn.click(); return 'clicked_div'; }
                
                btn = document.querySelector('[data-testid="cookie-policy-manage-dialog-accept-button"]');
                if (btn) { btn.click(); return 'clicked_testid'; }
                
                return 'not_found';
            })();
            """
            
            result = self.driver.execute_script(js_click_cookie)
            if result and result != 'not_found':
                log(f"Cookie consent accepted ({result})", "OK")
                self.cookie_handled = True
                time.sleep(0.5)
                return True
            return False
        except:
            return False
    
    def step1_open_recovery_page(self, phone=""):
        """Step 1: Open Facebook Identify Page"""
        log(f"Step 1: Opening Facebook Identify [{phone}]...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = "https://www.facebook.com/login/identify/?ctx=recover&from_login_screen=0"
                self.driver.get(url)
                time.sleep(3)
                
                # Handle cookies
                self._handle_cookie_consent()
                
                # Check if page loaded
                if "facebook.com" in self.driver.current_url:
                    log("Page loaded successfully!", "OK")
                    return True
                    
            except Exception as e:
                log(f"Attempt {attempt+1}/{max_retries} failed: {e}", "WARN")
                time.sleep(3)
        
        return False
    
    def step2_enter_phone(self, number):
        """Step 2: Enter phone number"""
        log(f"Step 2: Entering phone [{number}]...")
        
        try:
            # Find input field
            input_field = None
            selectors = [
                "input#identify_email",
                "input[name='email']",
                "input[type='text']"
            ]
            
            for selector in selectors:
                try:
                    input_field = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if input_field:
                        log(f"Found input: {selector}", "OK")
                        break
                except:
                    continue
            
            if not input_field:
                log("Could not find input field!", "ERROR")
                return False
            
            # Clear and type number
            input_field.clear()
            time.sleep(0.3)
            
            for char in number:
                input_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.1))
            
            log(f"Entered number: {number}", "OK")
            return True
            
        except Exception as e:
            log(f"Failed to enter phone: {e}", "ERROR")
            return False
    
    def step3_click_search(self, phone=""):
        """Step 3: Click search by pressing Enter"""
        log(f"Step 3: Submitting Search [{phone}]...")
        
        try:
            # Find input and press Enter
            input_field = self.driver.find_element(By.CSS_SELECTOR, "input#identify_email, input[name='email']")
            input_field.send_keys(Keys.ENTER)
            log("Sent ENTER key!", "OK")
            
            time.sleep(5)
            
            # Check if page changed
            page_source = self.driver.page_source
            if "This is my account" in page_source or "هذا حسابي" in page_source:
                log("Search successful - found account!", "OK")
                return True
            elif "No results found" in page_source or "لم يتم العثور" in page_source:
                log("No account found", "WARN")
                return "NOT_FOUND"
            
            log("Page may have changed", "OK")
            return True
            
        except Exception as e:
            log(f"Search failed: {e}", "ERROR")
            return False
    
    def step4_check_account_found(self, phone=""):
        """Step 4: Check if account was found"""
        log(f"Step 4: Checking account result [{phone}]...")
        
        try:
            page_source = self.driver.page_source
            
            # Check for multiple accounts
            if "Select your account" in page_source or "اختر حسابك" in page_source:
                log("Multiple accounts found!", "INFO")
                # Click first option
                try:
                    first_option = self.driver.find_element(By.CSS_SELECTOR, "div[role='radio'], div.x1n2onr6")
                    first_option.click()
                    time.sleep(2)
                    return True
                except:
                    pass
            
            # Check for single account
            if "This is my account" in page_source or "هذا حسابي" in page_source:
                log("Single account found!", "OK")
                return True
            
            # Check for not found
            if "No results found" in page_source or "لم يتم العثور" in page_source or "try again" in page_source.lower():
                log("Account NOT FOUND", "WARN")
                return "NOT_FOUND"
            
            return True
            
        except Exception as e:
            log(f"Check failed: {e}", "ERROR")
            return False
    
    def step5_select_sms_option(self, number):
        """Step 5: Select SMS option"""
        log(f"Step 5: Selecting SMS option [{number}]...")
        
        try:
            page_source = self.driver.page_source
            
            # Look for SMS option containing the number
            last_digits = number[-4:] if len(number) >= 4 else number
            
            # Try to find and click SMS option
            js_find_sms = f"""
            (function() {{
                let options = document.querySelectorAll('div[role="radio"], div.x1n2onr6, label');
                for (let opt of options) {{
                    let text = opt.innerText || opt.textContent || '';
                    if (text.includes('{last_digits}') || text.includes('SMS') || text.includes('رسالة')) {{
                        opt.click();
                        return 'clicked_sms';
                    }}
                }}
                return 'not_found';
            }})();
            """
            
            result = self.driver.execute_script(js_find_sms)
            
            if result == 'clicked_sms':
                log("SMS option selected!", "OK")
                time.sleep(2)
                return True
            else:
                log("SMS option not found", "WARN")
                return False
                
        except Exception as e:
            log(f"SMS selection failed: {e}", "ERROR")
            return False
    
    def step6_send_code(self):
        """Step 6: Click Continue/Send Code"""
        log("Step 6: Clicking Continue/Send Code...")
        
        try:
            # Find continue button
            js_find_continue = """
            (function() {
                let buttons = document.querySelectorAll('div[role="button"], button');
                for (let btn of buttons) {
                    let text = btn.innerText || btn.textContent || '';
                    if (text.includes('Continue') || text.includes('متابعة') || text.includes('Send') || text.includes('إرسال')) {
                        btn.click();
                        return 'clicked';
                    }
                }
                return 'not_found';
            })();
            """
            
            result = self.driver.execute_script(js_find_continue)
            
            if result == 'clicked':
                log("Continue button clicked!", "OK")
                time.sleep(5)
                
                # Check for success
                page_source = self.driver.page_source
                if "Enter the code" in page_source or "أدخل الرمز" in page_source or "We sent" in page_source:
                    log("OTP SENT SUCCESSFULLY!", "SUCCESS")
                    return "OTP_SENT"
                
                return True
            else:
                log("Continue button not found", "WARN")
                return False
                
        except Exception as e:
            log(f"Send code failed: {e}", "ERROR")
            return False
    
    def send_otp(self, phone):
        """Main OTP flow"""
        print(f"\n{'='*60}")
        print(f"   Facebook OTP (Scraping Browser) - {phone}")
        print(f"{'='*60}\n")
        
        try:
            # Setup remote browser
            if not self._setup_driver():
                return False, "DRIVER_FAILED"
            
            # Check IP
            self.check_ip()
            
            # Step 1: Open page
            if not self.step1_open_recovery_page(phone):
                return False, "PAGE_FAILED"
            
            # Step 2: Enter phone
            if not self.step2_enter_phone(phone):
                return False, "INPUT_FAILED"
            
            # Step 3: Search
            result = self.step3_click_search(phone)
            if result == "NOT_FOUND":
                return False, "NOT_FOUND"
            if not result:
                return False, "SEARCH_FAILED"
            
            # Step 4: Check account
            result = self.step4_check_account_found(phone)
            if result == "NOT_FOUND":
                return False, "NOT_FOUND"
            if not result:
                return False, "ACCOUNT_CHECK_FAILED"
            
            # Step 5: Select SMS
            if not self.step5_select_sms_option(phone):
                return False, "SMS_SELECT_FAILED"
            
            # Step 6: Send code
            result = self.step6_send_code()
            if result == "OTP_SENT":
                return True, "OTP_SENT"
            if not result:
                return False, "SEND_FAILED"
            
            return True, "COMPLETED"
            
        except Exception as e:
            log(f"Error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False, str(e)
            
        finally:
            self._close_driver()


def format_phone(phone):
    """Format phone number"""
    return phone.strip().replace(" ", "").replace("-", "")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fb_otp_scraping_browser.py <phone_number>")
        sys.exit(1)
    
    phone = format_phone(sys.argv[1])
    print(f"Testing Scraping Browser with: {phone}")
    
    bot = FacebookOTPScrapingBrowser()
    success, result = bot.send_otp(phone)
    
    print(f"\n{'='*60}")
    print(f"Final Result: Success={success}, Result={result}")
    print(f"{'='*60}")
