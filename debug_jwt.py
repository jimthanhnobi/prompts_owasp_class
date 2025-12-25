"""
Debug JWT Token - Kiểm tra token có hợp lệ không
"""
import base64
import json
import sys

def decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload without verification"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {"error": "Invalid JWT format"}
        
        # Decode payload (part 2)
        payload = parts[1]
        # Add padding if needed
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        return {"error": str(e)}

def main():
    # Load token from config
    with open("test_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    token = config["test_identity"]["user"]["jwt_token"]
    
    print("=" * 60)
    print("JWT Token Debug")
    print("=" * 60)
    
    print(f"\nToken (first 50 chars): {token[:50]}...")
    print(f"Token length: {len(token)}")
    
    payload = decode_jwt_payload(token)
    print(f"\nDecoded Payload:")
    print(json.dumps(payload, indent=2))
    
    # Check expiration
    import time
    if "exp" in payload:
        exp_time = payload["exp"]
        current_time = int(time.time())
        if exp_time > current_time:
            print(f"\n✅ Token NOT expired (expires in {(exp_time - current_time) // 3600} hours)")
        else:
            print(f"\n❌ Token EXPIRED {(current_time - exp_time) // 3600} hours ago")
    
    # Check issuer
    if payload.get("iss") == "vietduc":
        print("✅ Issuer matches: vietduc")
    else:
        print(f"❌ Issuer mismatch: {payload.get('iss')} != vietduc")
    
    print("\n" + "=" * 60)
    print("Server JWT Config (from application.yaml):")
    print("  secretKey: secret")
    print("  issuer: vietduc")
    print("=" * 60)
    
    print("\n⚠️  NOTE: If the token was signed with a different secret key,")
    print("   the server will reject it even if issuer matches!")
    print("\n   To fix: Generate a new token using the server's secret key 'secret'")
    print("   Or: Update server's jwt.secretKey to match the token's signing key")

if __name__ == "__main__":
    main()
