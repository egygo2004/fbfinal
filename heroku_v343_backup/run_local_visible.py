import os
import sys
import time
from fb_otp_browser import FacebookOTPBrowser

# Enable visible browser
HEADLESS = False

# Number to test
PHONE = "01550504273"

if __name__ == "__main__":
    print(f"Starting Local Visible Browser Test for {PHONE}...")
    
    # Initialize browser
    # We pass headless=False explicitly
    bot = FacebookOTPBrowser(headless=HEADLESS)
    
    try:
        # Run OTP flow
        success, result = bot.send_otp(PHONE)
        print(f"Final Result: Success={success}, Result={result}")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Keep browser open for a bit to see result
        print("Test finished. Keeping browser open for 60 seconds...")
        time.sleep(60)
        if hasattr(bot, 'driver') and bot.driver:
            bot.driver.quit()
