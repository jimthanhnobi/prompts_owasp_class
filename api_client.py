"""
API Client for MoneyCare Chatbot
Simulates real user interaction with the chatbot system

Supports 3 modes:
1. guest_new: Create new guest for each test (default)
2. guest_existing: Use existing guest with known fingerprint/guest_id
3. user: Test as authenticated user with JWT token
"""
import requests
import time
import json
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import uuid
from http.cookiejar import CookieJar

from config import TestConfig


@dataclass
class APIResponse:
    """API Response wrapper"""
    success: bool
    status_code: int
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    latency_ms: int
    raw_response: Optional[str] = None


@dataclass 
class TestIdentity:
    """Identity configuration for testing"""
    mode: str = "guest_new"  # guest_new | guest_existing | user
    
    # For guest_existing mode
    fingerprint: Optional[str] = None
    guest_id: Optional[str] = None
    
    # For user mode
    jwt_token: Optional[str] = None
    user_id: Optional[str] = None
    
    @classmethod
    def guest_new(cls) -> "TestIdentity":
        """Create new guest for each test"""
        return cls(mode="guest_new")
    
    @classmethod
    def guest_existing(cls, fingerprint: str = None, guest_id: str = None) -> "TestIdentity":
        """Use existing guest"""
        return cls(mode="guest_existing", fingerprint=fingerprint, guest_id=guest_id)
    
    @classmethod
    def user(cls, jwt_token: str, user_id: str = None) -> "TestIdentity":
        """Test as authenticated user"""
        return cls(mode="user", jwt_token=jwt_token, user_id=user_id)
    
    @classmethod
    def from_config_file(cls, config_path: str = "test_config.json") -> "TestIdentity":
        """Load identity from config file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            identity_config = config.get("test_identity", {})
            mode = identity_config.get("mode", "guest_new")
            
            if mode == "guest_new":
                return cls.guest_new()
            elif mode == "guest_existing":
                guest_config = identity_config.get("guest_existing", {})
                return cls.guest_existing(
                    fingerprint=guest_config.get("fingerprint"),
                    guest_id=guest_config.get("guest_id")
                )
            elif mode == "user":
                user_config = identity_config.get("user", {})
                return cls.user(
                    jwt_token=user_config.get("jwt_token"),
                    user_id=user_config.get("user_id")
                )
            else:
                return cls.guest_new()
        except Exception as e:
            print(f"Warning: Could not load test_config.json: {e}")
            return cls.guest_new()


class MoneyCareAPIClient:
    """
    Client for interacting with MoneyCare Chatbot API
    
    Supports 3 modes:
    1. guest_new: Create new guest for each test (default)
    2. guest_existing: Use existing guest with known fingerprint/guest_id  
    3. user: Test as authenticated user with JWT token
    
    Usage:
        # Mode 1: New guest (default)
        client = MoneyCareAPIClient(config)
        
        # Mode 2: Existing guest
        identity = TestIdentity.guest_existing(fingerprint="abc123", guest_id="uuid")
        client = MoneyCareAPIClient(config, identity)
        
        # Mode 3: Authenticated user
        identity = TestIdentity.user(jwt_token="eyJ...", user_id="uuid")
        client = MoneyCareAPIClient(config, identity)
        
        # Mode 4: Load from config file
        identity = TestIdentity.from_config_file("test_config.json")
        client = MoneyCareAPIClient(config, identity)
    """
    
    def __init__(self, config: TestConfig, identity: TestIdentity = None):
        self.config = config
        self.identity = identity or TestIdentity.guest_new()
        self.session = requests.Session()  # Maintains cookies automatically
        
        # Identity info (populated after init_session)
        self.owner_id: Optional[str] = None
        self.owner_type: Optional[str] = None  # "guest" or "user"
        self.conversation_id: Optional[str] = None
        
        # Setup based on identity mode
        self._setup_identity()
    
    def _setup_identity(self):
        """Setup client based on identity mode"""
        if self.identity.mode == "guest_new":
            # Generate new fingerprint
            self.fingerprint = self._generate_fingerprint()
            self.jwt_token = None
            print(f"[Identity] Mode: guest_new, fingerprint: {self.fingerprint}")
            
        elif self.identity.mode == "guest_existing":
            # Use existing fingerprint or generate one
            self.fingerprint = self.identity.fingerprint or self._generate_fingerprint()
            self.jwt_token = None
            if self.identity.guest_id:
                self.owner_id = self.identity.guest_id
                self.owner_type = "guest"
            print(f"[Identity] Mode: guest_existing, fingerprint: {self.fingerprint}, guest_id: {self.identity.guest_id}")
            
        elif self.identity.mode == "user":
            # Use JWT token for authenticated user
            self.fingerprint = self._generate_fingerprint()  # Still need fingerprint
            self.jwt_token = self.identity.jwt_token
            if self.identity.user_id:
                self.owner_id = self.identity.user_id
                self.owner_type = "user"
            print(f"[Identity] Mode: user, user_id: {self.identity.user_id}, has_token: {bool(self.jwt_token)}")
            
            # Set cookie for JWT authentication
            self._setup_cookies()
    
    def _generate_fingerprint(self) -> str:
        """Generate a unique fingerprint for this test session"""
        return f"test_fp_{uuid.uuid4().hex[:16]}"
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers matching real client behavior
        
        Headers used by the system:
        - X-Fingerprint: Browser fingerprint for guest identification
        - X-Owner-Id: Optional, for explicit owner identification
        - Cookie: ACCESS_TOKEN for authenticated users, GUEST_ID for guests
        
        Note: JWT token is sent via Cookie, NOT Authorization header!
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Fingerprint": self.fingerprint,
        }
        
        # Add owner ID if we have it
        if self.owner_id:
            headers["X-Owner-Id"] = self.owner_id
        
        return headers
    
    def _setup_cookies(self):
        """Setup cookies for authentication"""
        if self.identity.mode == "user" and self.jwt_token:
            # Set ACCESS_TOKEN cookie for authenticated user
            self.session.cookies.set("ACCESS_TOKEN", self.jwt_token)
            print(f"[Identity] Set ACCESS_TOKEN cookie for user authentication")
    
    def set_jwt_token(self, token: str):
        """
        Set JWT token for testing as authenticated user
        
        To test as a real user:
        1. Login to the system and get JWT token
        2. Call client.set_jwt_token(token)
        3. Run tests - will behave as that user
        """
        self.jwt_token = token
    
    def init_session(self) -> APIResponse:
        """
        Initialize a new session - MUST be called first
        
        Flow:
        1. Send GET /api/init-session with X-Fingerprint
        2. Server creates/finds guest or identifies user via JWT
        3. Server returns ownerId, ownerType, conversationId
        4. Server sets GUEST_ID cookie (stored in session automatically)
        
        Response format:
        {
            "ownerId": "uuid",
            "ownerType": "guest" | "user",
            "conversationId": "uuid",
            "username": "..." (if user),
            "firstName": "..." (if user),
            "lastName": "..." (if user)
        }
        """
        url = f"{self.config.chatbot_base_url}{self.config.init_session_endpoint}"
        
        start_time = time.time()
        try:
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=self.config.default_timeout_ms / 1000
            )
            latency_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                
                # Store identity info - handle both old and new response formats
                # New format: user_id, GUEST_ID, sessionType, conversation_id
                # Old format: ownerId, guestId, ownerType, conversationId
                self.owner_id = (
                    data.get("user_id") or 
                    data.get("ownerId") or 
                    data.get("GUEST_ID") or 
                    data.get("guestId")
                )
                self.owner_type = data.get("sessionType") or data.get("ownerType", "guest")
                self.conversation_id = data.get("conversation_id") or data.get("conversationId")
                
                # Check if authenticated
                is_authenticated = data.get("authenticated", False)
                username = data.get("username")
                
                print(f"[Session] Initialized as {self.owner_type}: {self.owner_id}")
                print(f"[Session] Authenticated: {is_authenticated}")
                if username:
                    print(f"[Session] Username: {username}")
                print(f"[Session] Conversation: {self.conversation_id}")
                print(f"[Session] Cookies: {dict(self.session.cookies)}")
                
                return APIResponse(
                    success=True,
                    status_code=response.status_code,
                    data=data,
                    error=None,
                    latency_ms=latency_ms,
                    raw_response=response.text
                )
            else:
                return APIResponse(
                    success=False,
                    status_code=response.status_code,
                    data=None,
                    error=f"HTTP {response.status_code}: {response.text}",
                    latency_ms=latency_ms,
                    raw_response=response.text
                )
                
        except requests.exceptions.Timeout:
            latency_ms = int((time.time() - start_time) * 1000)
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                error="Request timeout",
                latency_ms=latency_ms
            )
        except requests.exceptions.ConnectionError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                error=f"Connection error: {str(e)}. Is the chatbot service running at {self.config.chatbot_base_url}?",
                latency_ms=latency_ms
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                error=str(e),
                latency_ms=latency_ms
            )
    
    def ask(self, question: str, conversation_id: Optional[str] = None) -> APIResponse:
        """
        Send a question to the chatbot
        
        Request:
        POST /api/ask
        Headers: X-Fingerprint, X-Owner-Id, Cookie (GUEST_ID)
        Body: { "question": "...", "conversationId": "..." }
        
        Response:
        {
            "success": true,
            "answer": "..." (text or JSON string),
            "guestId": "uuid",
            "conversationId": "uuid",
            "messageId": "uuid"
        }
        """
        url = f"{self.config.chatbot_base_url}{self.config.ask_endpoint}"
        
        payload = {
            "question": question,
            "conversationId": conversation_id or self.conversation_id
        }
        
        start_time = time.time()
        try:
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self.config.default_timeout_ms / 1000
            )
            latency_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                
                # Update conversation ID if returned
                if data.get("conversationId"):
                    self.conversation_id = data.get("conversationId")
                
                return APIResponse(
                    success=True,
                    status_code=response.status_code,
                    data=data,
                    error=None,
                    latency_ms=latency_ms,
                    raw_response=response.text
                )
            elif response.status_code == 429:
                # Rate limit / message limit exceeded
                return APIResponse(
                    success=False,
                    status_code=response.status_code,
                    data=response.json() if response.text else None,
                    error="Rate limit exceeded",
                    latency_ms=latency_ms,
                    raw_response=response.text
                )
            else:
                return APIResponse(
                    success=False,
                    status_code=response.status_code,
                    data=None,
                    error=f"HTTP {response.status_code}: {response.text}",
                    latency_ms=latency_ms,
                    raw_response=response.text
                )
                
        except requests.exceptions.Timeout:
            latency_ms = int((time.time() - start_time) * 1000)
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                error="Request timeout",
                latency_ms=latency_ms
            )
        except requests.exceptions.ConnectionError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                error=f"Connection error: {str(e)}",
                latency_ms=latency_ms
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                error=str(e),
                latency_ms=latency_ms
            )
    
    def get_conversations(self) -> APIResponse:
        """Get all conversations for current user/guest"""
        url = f"{self.config.chatbot_base_url}/api/conversations"
        
        start_time = time.time()
        try:
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=self.config.default_timeout_ms / 1000
            )
            latency_ms = int((time.time() - start_time) * 1000)
            
            return APIResponse(
                success=response.status_code == 200,
                status_code=response.status_code,
                data=response.json() if response.status_code == 200 else None,
                error=None if response.status_code == 200 else response.text,
                latency_ms=latency_ms,
                raw_response=response.text
            )
        except Exception as e:
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                error=str(e),
                latency_ms=int((time.time() - start_time) * 1000)
            )
    
    def get_messages(self, conversation_id: str) -> APIResponse:
        """Get all messages in a conversation"""
        url = f"{self.config.chatbot_base_url}/api/conversations/{conversation_id}/messages"
        
        start_time = time.time()
        try:
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=self.config.default_timeout_ms / 1000
            )
            latency_ms = int((time.time() - start_time) * 1000)
            
            return APIResponse(
                success=response.status_code == 200,
                status_code=response.status_code,
                data=response.json() if response.status_code == 200 else None,
                error=None if response.status_code == 200 else response.text,
                latency_ms=latency_ms,
                raw_response=response.text
            )
        except Exception as e:
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                error=str(e),
                latency_ms=int((time.time() - start_time) * 1000)
            )
    
    def reset_session(self):
        """
        Reset session for new test
        Behavior depends on identity mode:
        - guest_new: Creates new fingerprint
        - guest_existing: Keeps same fingerprint
        - user: Keeps JWT token and re-sets cookie
        """
        self.session = requests.Session()
        self.conversation_id = None
        
        if self.identity.mode == "guest_new":
            # New guest = new fingerprint
            self.fingerprint = self._generate_fingerprint()
            self.owner_id = None
            self.owner_type = None
        elif self.identity.mode == "guest_existing":
            # Keep fingerprint to maintain guest identity
            self.owner_id = self.identity.guest_id
        elif self.identity.mode == "user":
            # Keep user identity and re-set cookie
            self.owner_id = self.identity.user_id
            self.owner_type = "user"
            # Re-set ACCESS_TOKEN cookie after session reset
            self._setup_cookies()
    
    def reset_session_keep_identity(self):
        """
        Reset session but keep same fingerprint
        Useful for testing session persistence
        """
        old_fingerprint = self.fingerprint
        self.session = requests.Session()
        self.owner_id = None
        self.owner_type = None
        self.conversation_id = None
        self.fingerprint = old_fingerprint
    
    def estimate_token_usage(self, question: str, answer: str) -> Dict[str, int]:
        """
        Estimate token usage from text length
        
        Rule of thumb:
        - English: ~4 characters per token
        - Vietnamese: ~2-3 characters per token (diacritics)
        - Mixed: ~3 characters per token (average)
        
        Returns: {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
        """
        # Estimate prompt tokens (question + system prompt overhead ~200 tokens)
        question_tokens = len(question) // 3
        system_overhead = 200  # Typical system prompt + formatting
        prompt_tokens = question_tokens + system_overhead
        
        # Estimate completion tokens
        completion_tokens = len(answer) // 3
        
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }
    
    def parse_bot_response(self, response_data: Dict[str, Any]) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Parse bot response to extract answer and transaction data
        
        Bot can return:
        1. Plain text (greeting, closing, unsupported, advice)
        2. JSON string (transaction result)
        
        Returns: (answer_text, parsed_transaction_dict)
        """
        answer = response_data.get("answer", "")
        parsed_transaction = None
        
        # Try to parse answer as JSON (for transaction responses)
        try:
            if answer and (answer.strip().startswith("{") or answer.strip().startswith("[")):
                json_data = json.loads(answer)
                
                if isinstance(json_data, dict):
                    if "transactions" in json_data:
                        # Transaction response format
                        txns = json_data.get("transactions", [])
                        if txns and len(txns) > 0:
                            tx = txns[0]
                            parsed_transaction = {
                                "transaction_type": tx.get("transaction_type"),
                                "amount": tx.get("amount"),
                                "currency": tx.get("currency", "VND"),
                                "category_id": tx.get("category_id"),
                                "category_name": tx.get("category_name"),
                                "transaction_date": tx.get("transaction_date"),
                                "description": tx.get("description"),
                                "member_id": tx.get("member_id"),
                                "display_name": tx.get("display_name"),
                                "confidence": tx.get("confidence"),
                                "transactions_count": len(txns),
                                "id": tx.get("id")  # Transaction ID from DB
                            }
                            
                            # Include summary and emotion if present
                            if "summary" in json_data:
                                parsed_transaction["summary"] = json_data["summary"]
                            if "emotion" in json_data:
                                parsed_transaction["emotion"] = json_data["emotion"]
                    
                    elif "error" in json_data:
                        # Error response
                        parsed_transaction = {"error": json_data.get("error")}
                        
        except json.JSONDecodeError:
            # Not JSON, just plain text response
            pass
        
        return answer, parsed_transaction


# Utility function for quick testing
def quick_test(base_url: str = "http://127.0.0.1:3333", message: str = "chi 50k ăn trưa"):
    """
    Quick test function to verify connection and basic functionality
    
    Usage:
        from api_client import quick_test
        quick_test()
        quick_test("http://staging:3333", "xin chào")
    """
    config = TestConfig(chatbot_base_url=base_url)
    client = MoneyCareAPIClient(config)
    
    print(f"\n{'='*60}")
    print(f"Quick Test - {base_url}")
    print(f"{'='*60}")
    
    # Init session
    print("\n1. Initializing session...")
    init_resp = client.init_session()
    if not init_resp.success:
        print(f"❌ Failed to init session: {init_resp.error}")
        return
    print(f"✅ Session initialized")
    print(f"   Owner: {client.owner_type} - {client.owner_id}")
    print(f"   Conversation: {client.conversation_id}")
    
    # Send message
    print(f"\n2. Sending message: '{message}'")
    ask_resp = client.ask(message)
    if not ask_resp.success:
        print(f"❌ Failed to send message: {ask_resp.error}")
        return
    
    print(f"✅ Response received in {ask_resp.latency_ms}ms")
    
    answer, parsed = client.parse_bot_response(ask_resp.data)
    print(f"\n3. Bot Response:")
    print(f"   {answer[:200]}..." if len(answer) > 200 else f"   {answer}")
    
    if parsed:
        print(f"\n4. Parsed Transaction:")
        for k, v in parsed.items():
            if v is not None:
                print(f"   {k}: {v}")
    
    print(f"\n{'='*60}")
    print("Quick test completed!")
    print(f"{'='*60}\n")
    
    return client, ask_resp


if __name__ == "__main__":
    # Run quick test when executed directly
    quick_test()
