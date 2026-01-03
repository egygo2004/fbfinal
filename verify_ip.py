from fb_otp_browser import FacebookOTPBrowser
import logging

# Ensure visible browser for verification
print("🚀 Starting Local Test with IP Check...")
bot = FacebookOTPBrowser(headless=False)

# Test Number
TEST_PHONE = "+201066373802" 

print(f"📱 Testing Number: {TEST_PHONE}")
bot.run_flow(TEST_PHONE)
print("✅ Test Complete")
