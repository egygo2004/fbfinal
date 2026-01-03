import urllib.request
import ssl

proxy = 'http://brd-customer-hl_90769934-zone-mobile_proxy1:p43u4hlvc8xi@brd.superproxy.io:33335'
url = 'https://geo.brdtest.com/welcome.txt?product=resi&method=native'

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({'https': proxy, 'http': proxy}),
    urllib.request.HTTPSHandler(context=ssl._create_unverified_context())
)

try:
    print(f"Testing proxy: {proxy}...")
    response = opener.open(url, timeout=10).read().decode()
    print("SUCCESS! Proxy Response:")
    print(response)
except Exception as e:
    print(f"Error: {e}")
