"""
Simple connection test to diagnose network issues
"""
import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://www.techsslaash.com/sitemap_index.xml"

print(f"Testing connection to: {url}\n")

# Test 1: Basic requests
print("=" * 50)
print("Test 1: Basic requests.get()")
print("=" * 50)
try:
    response = requests.get(url, timeout=10, verify=False)
    print(f"✓ SUCCESS!")
    print(f"  Status Code: {response.status_code}")
    print(f"  Content Length: {len(response.text)} bytes")
    print(f"  First 200 chars: {response.text[:200]}")
except Exception as e:
    print(f"✗ FAILED: {e}")

# Test 2: With headers
print("\n" + "=" * 50)
print("Test 2: With browser headers")
print("=" * 50)
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    response = requests.get(url, headers=headers, timeout=10, verify=False)
    print(f"✓ SUCCESS!")
    print(f"  Status Code: {response.status_code}")
    print(f"  Content Length: {len(response.text)} bytes")
except Exception as e:
    print(f"✗ FAILED: {e}")

# Test 3: Test if it's SSL specific
print("\n" + "=" * 50)
print("Test 3: HTTP instead of HTTPS")
print("=" * 50)
http_url = url.replace('https://', 'http://')
try:
    response = requests.get(http_url, timeout=10)
    print(f"✓ SUCCESS!")
    print(f"  Status Code: {response.status_code}")
except Exception as e:
    print(f"✗ FAILED: {e}")

print("\n" + "=" * 50)
print("DIAGNOSIS")
print("=" * 50)
print("If ALL tests failed:")
print("  → Firewall/Antivirus is blocking Python connections")
print("  → Corporate network blocking external access")
print("  → VPN/Proxy required")
print("\nIf only HTTPS failed:")
print("  → SSL/TLS configuration issue")
print("\nSUGGESTIONS:")
print("  1. Temporarily disable antivirus/firewall")
print("  2. Check if VPN is required")
print("  3. Try a different network")
print("  4. Test with a different website")
