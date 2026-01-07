import re

# Read file
with open('fb_otp_browser.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the problematic webdriver initialization code and replace it
old_code = '''        try:
            if ChromeDriverManager:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options, seleniumwire_options=seleniumwire_options)
            else:
                self.driver = webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)'''

new_code = '''        try:
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
                self.driver = webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)'''

content = content.replace(old_code, new_code)

# Write back
with open('fb_otp_browser.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed ChromeDriver initialization for Heroku!")
print("Added: /app/.chrome-for-testing/chromedriver-linux64/chromedriver priority")
