"""
IvaSMS Range Analyzer
=====================
This script analyzes which phone ranges on IvaSMS actually receive SMS
and which ranges are recommended for Facebook OTP testing.
"""

import requests
import json
from collections import defaultdict
from datetime import datetime, timedelta

# IvaSMS API Configuration - Update with your API URL
IVASMS_API_URL = "http://localhost:5000"  # Change to your deployed API URL

def analyze_ranges(days_back=30):
    """Analyze which ranges received the most SMS in the past N days"""
    
    print(f"🔍 Analyzing SMS data for the last {days_back} days...")
    print("=" * 60)
    
    range_stats = defaultdict(lambda: {'count': 0, 'paid': 0, 'revenue': 0})
    
    # Check last N days
    for i in range(days_back):
        date = (datetime.now() - timedelta(days=i)).strftime('%d/%m/%Y')
        try:
            response = requests.get(f"{IVASMS_API_URL}/sms?date={date}", timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'sms_details' in data:
                    for detail in data['sms_details']:
                        range_name = detail.get('country_number', 'Unknown')
                        range_stats[range_name]['count'] += int(detail.get('count', 0))
                        range_stats[range_name]['paid'] += int(detail.get('paid', 0))
                        range_stats[range_name]['revenue'] += float(detail.get('revenue', 0))
                    print(f"  ✅ {date}: {len(data['sms_details'])} ranges found")
        except Exception as e:
            print(f"  ❌ {date}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("📊 TOP RANGES BY SMS RECEIVED:")
    print("=" * 60)
    
    # Sort by count
    sorted_ranges = sorted(range_stats.items(), key=lambda x: x[1]['count'], reverse=True)
    
    for i, (range_name, stats) in enumerate(sorted_ranges[:20], 1):
        print(f"{i:2}. {range_name}")
        print(f"    📱 Total SMS: {stats['count']}")
        print(f"    💰 Paid: {stats['paid']} | Revenue: ${stats['revenue']:.2f}")
        print()
    
    return sorted_ranges


def get_best_numbers_from_range(range_prefix, date=None):
    """Get actual phone numbers from the best performing range"""
    
    if date is None:
        date = datetime.now().strftime('%d/%m/%Y')
    
    print(f"\n🔍 Fetching numbers from range: {range_prefix}")
    
    try:
        response = requests.get(f"{IVASMS_API_URL}/sms?date={date}", timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'otp_messages' in data:
                for msg in data['otp_messages']:
                    if msg['range'] == range_prefix:
                        print(f"  📱 {msg['phone_number']}: {msg['otp_message'][:50]}...")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def analyze_local_results(log_file_or_folder):
    """Analyze local OTP script results to see success rate by range"""
    import os
    import glob
    
    print(f"\n📊 Analyzing local OTP results...")
    print("=" * 60)
    
    results = {
        'otp_sent': [],
        'not_found': [],
        'no_sms_option': [],
        'unknown': []
    }
    
    # Find all cookie files (these indicate OTP_SENT success)
    cookie_files = glob.glob(os.path.join(log_file_or_folder, "cookies_*.json"))
    for f in cookie_files:
        phone = os.path.basename(f).replace("cookies_", "").replace(".json", "")
        results['otp_sent'].append(phone)
    
    # Find not_found screenshots
    not_found_files = glob.glob(os.path.join(log_file_or_folder, "step_not_found*.png"))
    # These are harder to match to phone numbers without parsing logs
    
    print(f"\n✅ OTP SENT (cookies saved): {len(results['otp_sent'])} numbers")
    
    # Analyze by range
    range_success = defaultdict(int)
    for phone in results['otp_sent']:
        # Get first 6 digits as range indicator
        if len(phone) >= 6:
            range_prefix = phone[:6]
            range_success[range_prefix] += 1
    
    print("\n📊 Success by Range Prefix:")
    for prefix, count in sorted(range_success.items(), key=lambda x: -x[1]):
        print(f"  {prefix}xxx: {count} successful OTPs")
    
    return results


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🔬 IvaSMS Range Analyzer")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--local":
            # Analyze local results
            folder = sys.argv[2] if len(sys.argv) > 2 else "./local"
            analyze_local_results(folder)
        elif sys.argv[1] == "--api":
            # Analyze from API
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            analyze_ranges(days)
    else:
        print("\nUsage:")
        print("  python range_analyzer.py --local [folder]  # Analyze local OTP results")
        print("  python range_analyzer.py --api [days]      # Analyze IvaSMS API data")
        print("\nExample:")
        print("  python range_analyzer.py --local ./local")
        print("  python range_analyzer.py --api 30")
