"""Test the sync API endpoint via HTTP."""
import requests
import json

print("Testing sync API endpoint...")
print("Make sure the Flask app is running on http://localhost:5000")
print()

try:
    # Test GET request first to verify server is running
    print("1. Testing server is alive...")
    response = requests.get('http://localhost:5000/api/tests/stats', timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   [OK] Server is responding")
    else:
        print(f"   [ERROR] Unexpected status code")
        exit(1)

    # Test POST to sync endpoint
    print("\n2. Testing sync endpoint...")
    response = requests.post('http://localhost:5000/api/sync', timeout=300)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:500]}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n   [OK] Sync successful!")
        print(f"   Status: {data.get('status')}")
        print(f"   Message: {data.get('message')}")
        if 'sync_log' in data:
            print(f"   Tests synced: {data['sync_log'].get('tests_synced')}")
    else:
        print(f"\n   [ERROR] Sync failed with status {response.status_code}")

except requests.exceptions.ConnectionError:
    print("   [ERROR] Could not connect to server")
    print("   Make sure Flask app is running: python app.py")
except requests.exceptions.Timeout:
    print("   [ERROR] Request timed out")
    print("   Sync operations can take a long time")
except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()

