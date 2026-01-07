import re

# Read file
with open('fb_otp_browser.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find where to insert (after options.add_argument("--disable-gpu"))
chrome_detection_code = '''
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
'''

# Insert after line with --disable-gpu
pattern = r'(options\.add_argument\("--disable-gpu"\))\r?\n'
replacement = r'\1\n' + chrome_detection_code + '\n'
content = re.sub(pattern, replacement, content, count=1)

# Write back
with open('fb_otp_browser.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Added Chrome detection code for Heroku!")
