"""
Direct test of JWT authentication
Gửi request trực tiếp với cookie ACCESS_TOKEN để debug
"""
import requests
import json

def test_with_cookie():
    """Test init-session với ACCESS_TOKEN cookie"""
    
    # Load config
    with open("test_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    jwt_token = config["test_identity"]["user"]["jwt_token"]
    user_id = config["test_identity"]["user"]["user_id"]
    
    print("=" * 60)
    print("Testing JWT Authentication via Cookie")
    print("=" * 60)
    
    # Create session
    session = requests.Session()
    
    # Set cookie BEFORE request
    session.cookies.set("ACCESS_TOKEN", jwt_token, domain="127.0.0.1", path="/")
    
    print(f"\nCookies set: {dict(session.cookies)}")
    print(f"Cookie ACCESS_TOKEN length: {len(session.cookies.get('ACCESS_TOKEN', ''))}")
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Fingerprint": "test_debug_fingerprint_123",
    }
    
    print(f"\nHeaders: {headers}")
    
    # Make request
    url = "http://127.0.0.1:3333/api/init-session"
    print(f"\nCalling: GET {url}")
    
    response = session.get(url, headers=headers)
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Cookies: {dict(response.cookies)}")
    print(f"\nResponse Body:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # Check if recognized as user
    data = response.json()
    owner_type = data.get("ownerType", "unknown")
    owner_id = data.get("ownerId") or data.get("guestId")
    
    print("\n" + "=" * 60)
    if owner_type == "user":
        print(f"✅ SUCCESS! Recognized as USER: {owner_id}")
    else:
        print(f"❌ FAILED! Recognized as {owner_type}: {owner_id}")
        print("\nPossible causes:")
        print("1. JWT secret key mismatch (server uses 'secret', token may use different key)")
        print("2. Cookie not being sent (check server logs)")
        print("3. Token verification failed (check server logs for 'JWT decode error')")
    print("=" * 60)

def test_with_header():
    """Test với Authorization header (để so sánh)"""
    
    with open("test_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    jwt_token = config["test_identity"]["user"]["jwt_token"]
    
    print("\n" + "=" * 60)
    print("Testing with Authorization Header (for comparison)")
    print("=" * 60)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Fingerprint": "test_debug_fingerprint_456",
        "Authorization": f"Bearer {jwt_token}"
    }
    
    url = "http://127.0.0.1:3333/api/init-session"
    response = requests.get(url, headers=headers)
    
    print(f"\nResponse Status: {response.status_code}")
    data = response.json()
    owner_type = data.get("ownerType", "unknown")
    print(f"Owner Type: {owner_type}")
    print("(Note: Server reads from Cookie, not Authorization header)")

if __name__ == "__main__":
    test_with_cookie()
    # test_with_header()
