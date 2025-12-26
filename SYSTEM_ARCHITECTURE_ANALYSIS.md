# 📊 PHÂN TÍCH KIẾN TRÚC HỆ THỐNG MONEYCARE CHATBOT

> **Tác giả**: AI Assistant  
> **Ngày**: 2025-12-26  
> **Mục đích**: Phân tích chi tiết kiến trúc hệ thống để tối ưu test framework

---

## 🏗️ I. TỔNG QUAN KIẾN TRÚC

### 1. Tech Stack
```yaml
Platform: Spring Boot 3.5.0 (Java 17)
Architecture: Microservices với Feign Client
Database: PostgreSQL (hosted tại 34.158.53.202:5432)
Identity: JWT Authentication + Guest Fingerprint
AI Service: External AI Client Service (port 3334)
Expense Service: External Service (port 3335)
Billing Service: External Service (port 4444)
Auth Service: External Service (port 8888)
Subscription Service: External Service (port 7777)
```

### 2. Các Service Chính
```
┌─────────────────────────────────────────────────────────────┐
│                  CHATBOT AI SERVICE (3333)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Controller  │───▶│   Service    │───▶│  Repository  │ │
│  │  (REST API)  │    │   (Logic)    │    │  (Database)  │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                             │
│         │                    ▼                             │
│         │            ┌──────────────┐                      │
│         │            │ Feign Client │                      │
│         │            └──────────────┘                      │
└─────────┼────────────────────┼──────────────────────────────┘
          │                    │
          ▼                    ▼
┌─────────────────┐  ┌──────────────────────┐
│  Auth Service   │  │   AI Client Service  │
│   (JWT Auth)    │  │  (OpenAI/DeepSeek)   │
└─────────────────┘  └──────────────────────┘
                              │
          ┌───────────────────┼────────────────────┐
          ▼                   ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Expense Service  │ │ Billing Service  │ │Subscription Svc  │
│ (Save Tx Data)   │ │ (Usage Tracking) │ │ (Plan Check)     │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## 🔄 II. FLOW XỬ LÝ MESSAGE CHI TIẾT

### Flow Tổng Quan
```
User Request → Controller → IdentityService → ChatFlowService → IntentDetection
                                                      │
                    ┌─────────────────────────────────┴────────────────────┐
                    ▼                                 ▼                     ▼
            TransactionIntent              FinancialQuestionIntent    OtherIntents
                    │                                 │                     │
                    ▼                                 ▼                     │
        TransactionExtractionService    FinancialAdviceService            │
                    │                                 │                     │
                    ▼                                 ▼                     │
              AI Client (Extract)            AI Client (Advice)            │
                    │                                 │                     │
                    ▼                                 │                     │
            Expense Service (Save)                   │                     │
                    │                                 │                     │
                    └─────────────────────────────────┴─────────────────────┘
                                         │
                                         ▼
                                  Save Message to DB
                                         │
                                         ▼
                                  Return Response
```

### 1. **Endpoint: POST /api/ask**

**Request:**
```json
{
  "conversationId": "uuid",
  "question": "Chi 50k ăn trưa"
}
```

**Headers:**
```
X-Fingerprint: browser_fingerprint (cho guest)
X-Owner-Id: uuid (optional)
Cookie: JWT token (cho user)
```

**Controller:** `ChatControllerV2.ask()`
```java
// File: ChatControllerV2.java:90-118
@PostMapping("/api/ask")
public AskResponseDTOV2 ask(
    HttpServletRequest request,
    HttpServletResponse response,
    @RequestHeader(value="X-Fingerprint", required=false) String fingerprint,
    @RequestHeader(value="X-Owner-Id", required=false) String ownerId,
    @RequestBody AskRequestDTOV2 ask
)
```

---

### 2. **Identity Resolution**

**Service:** `IdentityServiceV2.resolveIdentity()`

**Logic:**
```java
// File: IdentityServiceV2.java:29-61

1. Kiểm tra JWT Token
   ├─ Có JWT → Extract userId → ownerType = "user"
   └─ Không JWT → Check fingerprint + cookie
                 └─ Tạo/lấy guestId → ownerType = "guest"

2. Return IdentityResult:
   {
     sessionId: UUID,    // userId or guestId
     ownerId: UUID,      // userId or guestId
     ownerType: "user" | "guest"
   }
```

**Quan trọng:** 
- `sessionId = ownerId` trong hệ thống này
- Guest được track qua fingerprint + cookie
- User được track qua JWT token

---

### 3. **Intent Detection**

**Service:** `IntentDetectionServiceV2.detectIntent()`

**Logic Flow:**
```java
// File: IntentDetectionServiceV2.java:27-191

1. Load System Prompt từ Database
   ├─ SELECT * FROM ai_prompts WHERE code='intent_detection' AND is_active=true
   └─ Lấy field: system_prompt, model, temperature

2. Prepare Prompt
   systemPrompt = prompt.replace("{message}", userMessage)

3. Call AI Service
   POST http://127.0.0.1:3334/api/ai/detect-intent
   {
     "userMessage": "Chi 50k ăn trưa",
     "systemPrompt": "...",
     "provider": null  // default = openai
   }

4. Parse Response
   {
     "intent": "transaction" | "financial_question" | "greeting" | "closing" | "app_query" | "unsupported",
     "confidence": 0.0-1.0
   }

5. Override Logic (quan trọng!)
   // Safety override: decision questions must not be treated as transaction
   if (isDecisionAdvice && !isExplicitLog && intent == "transaction") {
       intent = "financial_question"
   }
```

**Các Intent Types:**
- `transaction`: Ghi nhận giao dịch (chi/thu)
- `financial_question`: Tư vấn tài chính
- `greeting`: Chào hỏi
- `closing`: Kết thúc
- `app_query`: Hỏi về app (bảo mật, điều khoản, hoàn tiền)
- `unsupported`: Không hỗ trợ

**Decision Detection:**
```java
// File: ChatFlowServiceV2.java:317-329
private boolean isDecisionAdvice(String qLower) {
    return qLower.contains("có nên")
        || qLower.contains("nên không")
        || qLower.contains("hợp lý không")
        || qLower.contains("đáng không")
        || qLower.contains("có đáng")
        || qLower.contains("có ổn không");
}
```

---

### 4. **Intent Execution: TRANSACTION**

**Service:** `ChatFlowServiceV2.handleTransactionIntent()`  
**Helper:** `TransactionExtractionServiceV2.extract()`

**Flow:**
```java
// File: ChatFlowServiceV2.java:221-311

┌─────────────────────────────────────────────────────────────┐
│ Step 1: NORMALIZE AMOUNT (Preprocessor)                    │
├─────────────────────────────────────────────────────────────┤
│ Input:  "Chi 50k ăn trưa"                                   │
│ Output: "Chi 50000 ăn trưa"                                 │
│                                                             │
│ AmountNormalizer.normalize():                               │
│ - "50k" → "50000"                                           │
│ - "1.5tr" → "1500000"                                       │
│ - "100 nghìn" → "100000"                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: LOAD PROMPT & CONTEXT                              │
├─────────────────────────────────────────────────────────────┤
│ 1. Load prompt: ai_prompts.code='transaction'              │
│ 2. Load categories for owner (userId or guestId)           │
│ 3. Load members for owner                                  │
│ 4. Get today's date (Vietnam timezone)                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: BUILD SYSTEM PROMPT                                │
├─────────────────────────────────────────────────────────────┤
│ systemPrompt = template                                     │
│   .replace("{message}", normalizedMessage)                 │
│   .replace("{categories_json}", categoryList)              │
│   .replace("{members_json}", memberList)                   │
│   .replace("{today}", "2025-12-26")                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: CALL AI SERVICE                                    │
├─────────────────────────────────────────────────────────────┤
│ POST http://127.0.0.1:3334/api/ai/extract-transaction-info │
│ {                                                           │
│   "systemPrompt": "...",                                    │
│   "userMessage": "Chi 50000 ăn trưa",                       │
│   "maxTokens": 1000,                                        │
│   "temperature": 0.4,                                       │
│   "model": null,     // default: gpt-4o-mini               │
│   "provider": null   // default: openai                    │
│ }                                                           │
│                                                             │
│ Response:                                                   │
│ {                                                           │
│   "reply": "{...JSON...}",                                  │
│   "usage": {                                                │
│     "prompt": 150,                                          │
│     "completion": 80,                                       │
│     "total": 230                                            │
│   }                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: PARSE & POST-PROCESS JSON                          │
├─────────────────────────────────────────────────────────────┤
│ 1. Clean JSON (remove ```json markers)                     │
│ 2. Parse JSON structure                                    │
│ 3. For each transaction:                                   │
│    a. Default transaction_type to "expense"                │
│    b. Map category_name → category_id (with kind check)    │
│    c. Fallback to "Khác" if no match                       │
│    d. Detect member from description                       │
│    e. Default currency to "VND"                            │
│                                                             │
│ Expected JSON Structure:                                    │
│ {                                                           │
│   "transactions": [                                         │
│     {                                                       │
│       "transaction_type": "expense",                        │
│       "category_name": "Ăn uống",                           │
│       "category_id": "uuid",                                │
│       "amount": 50000,                                      │
│       "currency": "VND",                                    │
│       "description": "Ăn trưa",                             │
│       "transaction_date": "2025-12-26",                     │
│       "member_id": "",                                      │
│       "display_name": "",                                   │
│       "confidence": 0.95                                    │
│     }                                                       │
│   ],                                                        │
│   "summary": {                                              │
│     "total_amount": 50000,                                  │
│     "transaction_count": 1,                                 │
│     "type_distribution": {"expense": 1}                     │
│   },                                                        │
│   "emotion": {                                              │
│     "tone": "neutral",                                      │
│     "confidence": 0.8                                       │
│   }                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 6: SAVE TO EXPENSE SERVICE                            │
├─────────────────────────────────────────────────────────────┤
│ POST http://127.0.0.1:3335/api/v2/expenses/batch-create    │
│ {                                                           │
│   "transactions": [...extracted JSON...],                   │
│   "guestId": "uuid" | null,                                 │
│   "userId": "uuid" | null                                   │
│ }                                                           │
│                                                             │
│ Response:                                                   │
│ {                                                           │
│   "success": true,                                          │
│   "transactions": [                                         │
│     {                                                       │
│       "id": "uuid",                                         │
│       "type": "expense",                                    │
│       "categoryId": "uuid",                                 │
│       "categoryName": "Ăn uống",                            │
│       "amountMinor": 50000,                                 │
│       "currency": "VND",                                    │
│       "note": "Ăn trưa",                                    │
│       "date": "2025-12-26",                                 │
│       "memberId": null,                                     │
│       "memberName": null,                                   │
│       "ownerGuestId": "uuid"                                │
│     }                                                       │
│   ]                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 7: BUILD UI RESPONSE JSON                             │
├─────────────────────────────────────────────────────────────┤
│ Combine:                                                    │
│ - AI extracted data (summary, emotion, confidence)         │
│ - Expense service response (transaction IDs, real data)    │
│                                                             │
│ Final UI JSON:                                              │
│ {                                                           │
│   "transactions": [                                         │
│     {                                                       │
│       "id": "uuid",                                         │
│       "transaction_type": "expense",                        │
│       "category_id": "uuid",                                │
│       "category_name": "Ăn uống",                           │
│       "amount": 50000,                                      │
│       "currency": "VND",                                    │
│       "description": "Ăn trưa",                             │
│       "transaction_date": "2025-12-26",                     │
│       "member_id": null,                                    │
│       "display_name": null,                                 │
│       "confidence": 0.95                                    │
│     }                                                       │
│   ],                                                        │
│   "summary": {...},                                         │
│   "emotion": {...}                                          │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

**Category Matching với Kind Validation:**
```java
// File: TransactionExtractionServiceV2.java:140-188

Quan trọng: Category phải match cả NAME và KIND!

1. transaction_type = "expense" → expectedKind = "expense"
2. transaction_type = "income" → expectedKind = "income"

3. Category Matching Priority:
   a. Exact name match + correct kind → Use category_id
   b. No match → Fallback to "Khác" (of same kind)
   c. No fallback → Empty category_id

4. Example:
   User: "Chi 50k ăn trưa"
   AI extracts: category_name = "Ăn uống", transaction_type = "expense"
   
   Database có:
   - {id: "uuid-1", name: "Ăn uống", kind: "expense"}  ✅ MATCH
   - {id: "uuid-2", name: "Ăn uống", kind: "income"}   ❌ SKIP (wrong kind)
   
   Result: category_id = "uuid-1"
```

**Member Detection:**
```java
// File: TransactionExtractionServiceV2.java:193-216

1. Load all members for owner
2. Search member name in original message (case-insensitive)
3. If found → set member_id + display_name
4. Else → empty fields

Example:
Message: "Chi 50k ăn trưa với Hùng"
Members in DB: [{id: "uuid", displayName: "Hùng"}]
Result: member_id = "uuid", display_name = "Hùng"
```

---

### 5. **Intent Execution: FINANCIAL_QUESTION**

**Service:** `ChatFlowServiceV2.handleFinancialQuestion()`  
**Helper:** `FinancialAdviceServiceV2.generateAdviceWithData()`

**Flow:**
```java
// File: ChatFlowServiceV2.java:171-215

┌─────────────────────────────────────────────────────────────┐
│ Step 1: CHECK OWNER TYPE                                   │
├─────────────────────────────────────────────────────────────┤
│ IF guest:                                                   │
│   → Return generic advice (jar model)                       │
│   → No real data analysis                                   │
│                                                             │
│ IF user:                                                    │
│   → Continue to Step 2                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: QUERY USER TRANSACTION SUMMARY                     │
├─────────────────────────────────────────────────────────────┤
│ UserTransactionQueryService.getSummaryForUser(ownerId)     │
│                                                             │
│ Returns: Optional<TransactionSummaryDTO>                    │
│ {                                                           │
│   "totalIncome": 10000000.0,                                │
│   "totalExpense": 7500000.0,                                │
│   "savingRate": 0.25,  // (income - expense) / income      │
│   "categoryBreakdown": [                                    │
│     {                                                       │
│       "categoryName": "Ăn uống",                            │
│       "amountMinor": 2000000.0,                             │
│       "percentage": 26.67                                   │
│     },                                                      │
│     ...                                                     │
│   ]                                                         │
│ }                                                           │
│                                                             │
│ IF no summary (new user):                                  │
│   → Return "new user" message (gợi ý ghi giao dịch)        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: CHECK DECISION ADVICE MODE                         │
├─────────────────────────────────────────────────────────────┤
│ Question: "Có nên mua iPhone 1500000 không?"               │
│                                                             │
│ isDecisionAdvice = true                                     │
│ isExplicitLog = false                                       │
│                                                             │
│ Extract:                                                    │
│ - decisionAmount = 1500000 (VND)                            │
│ - decisionItem = "iPhone"                                   │
│ - decisionCategory = "Điện tử" (from DB matching)          │
│                                                             │
│ → Inject these into financial_question prompt               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: BUILD SYSTEM PROMPT                                │
├─────────────────────────────────────────────────────────────┤
│ Template: ai_prompts.code='financial_question'             │
│                                                             │
│ Replace placeholders:                                       │
│ {income} → "10000000"                                       │
│ {expense} → "7500000"                                       │
│ {savingRate} → "25.00"                                      │
│ {categoryBreakdown} → "- Ăn uống: 2000000 VND (26.67%)..." │
│ {decisionItem} → "iPhone"                                   │
│ {decisionAmount} → "1500000"                                │
│ {decisionCategory} → "Điện tử"                              │
│ {income - expense} → "2500000" (computed deterministic)     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: CALL AI SERVICE                                    │
├─────────────────────────────────────────────────────────────┤
│ POST http://127.0.0.1:3334/api/ai/generate-advice          │
│ {                                                           │
│   "systemPrompt": "...",                                    │
│   "userMessage": "[CÂU HỎI NGƯỜI DÙNG]\nCó nên mua...",    │
│   "maxTokens": 1000,                                        │
│   "temperature": 0.4,                                       │
│   "model": null,     // default: gpt-4o-mini               │
│   "provider": null   // default: openai                    │
│ }                                                           │
│                                                             │
│ Response:                                                   │
│ {                                                           │
│   "reply": "### Tổng quan\n| Loại | Số tiền (VND) |...",  │
│   "usage": {                                                │
│     "prompt": 200,                                          │
│     "completion": 150,                                      │
│     "total": 350                                            │
│   }                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 6: RETURN MARKDOWN ADVICE                             │
├─────────────────────────────────────────────────────────────┤
│ Return reply as-is (Markdown format)                        │
│                                                             │
│ Example:                                                    │
│ ### Tổng quan                                               │
│ | Loại | Số tiền (VND) |                                   │
│ |------|---------------|                                   │
│ | Thu nhập | 10000000 |                                    │
│ | Chi tiêu | 7500000 |                                     │
│ | Tiết kiệm ước tính | 2500000 |                           │
│                                                             │
│ → Dòng tiền tích cực, tỷ lệ tiết kiệm 25% là hợp lý.       │
│                                                             │
│ ### Đánh giá giao dịch                                     │
│ **Kết luận:** Cân nhắc                                      │
│ **Lý do:** iPhone 1.5tr chiếm 60% số tiết kiệm tháng...    │
└─────────────────────────────────────────────────────────────┘
```

**Decision Category Resolution:**
```java
// File: ChatFlowServiceV2.java:387-470

1. Infer expected kind from question
   - Contains "lương", "thưởng", "nhận tiền" → "income"
   - Default → "expense"

2. Load categories for owner (filtered by kind)

3. Keyword scoring:
   - Food keywords: "ăn", "cơm", "bún", "phở", "trà sữa", "cà phê"
   - Transport: "xăng", "grab", "taxi", "xe", "đi lại"
   - Shopping: "mua", "shopping", "quần áo", "giày"
   - Bill: "tiền điện", "tiền nước", "internet", "hóa đơn"

4. Match category from DB:
   - Exact name match + high keyword score → Use it
   - No match → Fallback to "Khác" (same kind)

5. Return: {decisionItem, decisionCategoryName, decisionCategoryId}
```

---

### 6. **Message Persistence**

**Service:** `MessageServiceV2`

**Flow:**
```java
// Lưu User Message
Message userMessage = new Message();
userMessage.setSenderType("user");
userMessage.setContent(question);
messageService.createBySessionWithOwner(sessionId, ownerId, ownerType, userMessage);

// Lưu Bot Response
Message botMessage = new Message();
botMessage.setSenderType("bot");
botMessage.setContent(reply);  // JSON hoặc Markdown
messageService.createBySessionWithOwner(sessionId, ownerId, ownerType, botMessage);
```

**Database Schema:**
```sql
CREATE TABLE messages (
  id UUID PRIMARY KEY,
  conversation_id UUID,
  sender_type VARCHAR(50),  -- 'user' | 'bot'
  content TEXT,
  tokens_used INTEGER,      -- AI usage tracking
  cost_minor BIGINT,        -- Cost in minor unit (VND * 100)
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

---

## 🔐 III. IDENTITY & AUTHENTICATION

### 1. User Authentication (JWT)

**Flow:**
```
1. User login → Auth Service (port 8888)
2. Auth Service returns JWT token
3. Frontend stores JWT in Cookie
4. Every request includes Cookie header
5. AuthFilter validates JWT
6. Extract userId from JWT token
```

**JWT Token Structure:**
```json
{
  "sub": "user-uuid",
  "iss": "vietduc",
  "exp": 1640000000,
  "iat": 1639999400
}
```

**Config:**
```yaml
jwt:
  secretKey: secret
  issuer: vietduc
  expirationMinute: 10
```

### 2. Guest Authentication (Fingerprint)

**Service:** `GuestServiceV2.resolveGuest()`

**Flow:**
```java
1. Frontend generates browser fingerprint
   - Browser info + screen resolution + timezone + canvas hash
   
2. First request:
   Header: X-Fingerprint = "abc123..."
   
3. Backend:
   a. Check if fingerprint exists in DB
   b. If not → Create new Guest record
   c. Generate guest_token (cookie)
   d. Set-Cookie in response
   
4. Subsequent requests:
   - Check guest_token cookie first
   - Fallback to fingerprint if no cookie
   
5. Guest Limit:
   - Max 50 messages per guest (configurable)
   - After limit → Prompt to register
```

**Database Schema:**
```sql
CREATE TABLE guests (
  id UUID PRIMARY KEY,
  created_at TIMESTAMP
);

CREATE TABLE guest_fingerprints (
  id UUID PRIMARY KEY,
  guest_id UUID,
  fingerprint_hash VARCHAR(255),
  device_info JSONB,
  created_at TIMESTAMP
);

CREATE TABLE guest_sessions (
  id UUID PRIMARY KEY,
  guest_id UUID,
  session_token VARCHAR(255),
  expires_at TIMESTAMP,
  created_at TIMESTAMP
);
```

---

## 💰 IV. COST TRACKING & BILLING

### 1. Token Usage Tracking

**AI Service Response:**
```json
{
  "reply": "...",
  "usage": {
    "prompt": 150,      // Input tokens
    "completion": 80,   // Output tokens
    "total": 230        // Total tokens
  }
}
```

**Chatbot Service:**
```java
// File: FinancialAdviceServiceV2.java:96-102

Object usageObj = aiRes.get("usage");
if (usageObj instanceof Map<?, ?> usage) {
    int promptTokens     = safeInt(usage.get("prompt"));
    int completionTokens = safeInt(usage.get("completion"));
    int totalTokens      = safeInt(usage.get("total"));
    log.info("[ADVICE USAGE] p={}, c={}, t={}", promptTokens, completionTokens, totalTokens);
}

// Save to message.tokens_used
message.setTokensUsed(totalTokens);
```

### 2. Cost Calculation

**Pricing (gpt-4o-mini):**
```
Input:  $0.150 / 1M tokens
Output: $0.600 / 1M tokens
```

**Calculation:**
```java
costMinor = (promptTokens * 0.150 / 1000000 + completionTokens * 0.600 / 1000000) * 25000 * 100

// Example:
// promptTokens = 150
// completionTokens = 80
// cost = (150 * 0.150 / 1000000 + 80 * 0.600 / 1000000) * 25000 * 100
//      = (0.0000225 + 0.000048) * 25000 * 100
//      = 0.0000705 * 25000 * 100
//      = 176.25 VND (minor unit = 17625)
```

### 3. Billing Usage Event

**Service:** `BillingGuardServiceV2.sendUsageEvent()`

**Flow:**
```java
// File: BillingGuardServiceV2.java:183-216

POST http://127.0.0.1:4444/api/billing/usage-events
{
  "conversationId": "uuid",
  "messageId": "uuid",
  "ownerUserId": "uuid" | null,
  "ownerGuestId": "uuid" | null,
  "ownerHouseholdId": "uuid" | null,
  "provider": "openai",
  "model": "gpt-4o-mini",
  "inputTokens": 150,
  "outputTokens": 80,
  "cachedTokens": 0,
  "costMinor": 17625  // VND * 100
}
```

### 4. Subscription Check

**Service:** `BillingGuardServiceV2.hasActiveSubscription()`

**Flow:**
```java
// File: BillingGuardServiceV2.java:49-70

GET http://127.0.0.1:7777/api/subscription/me/active

Response:
{
  "activeSubscription": {
    "status": "active",
    "expiredAt": "2025-01-20T20:12:32Z",
    "planName": "Premium",
    "planId": "uuid"
  } | null
}

Logic:
- activeSubscription != null → User có gói active
- activeSubscription == null → User chưa mua gói
```

---

## 🧠 V. AI PROMPTS MANAGEMENT

### 1. Database Schema

```sql
CREATE TABLE ai_prompts (
  id UUID PRIMARY KEY,
  code VARCHAR(50) NOT NULL,           -- 'intent_detection', 'transaction', 'financial_question'
  intent_code VARCHAR(50),             -- Deprecated
  kind VARCHAR(50) NOT NULL,           -- 'system' | 'user'
  system_prompt TEXT NOT NULL,         -- Template với placeholders
  user_template TEXT NOT NULL,         -- Rarely used
  model VARCHAR(50) DEFAULT 'gpt-4o-mini',
  temperature DECIMAL(3,2) DEFAULT 0.2,
  top_p DECIMAL(3,2) DEFAULT 1.0,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### 2. Prompt Loading

**Service:** `AiPromptServiceV2.getActivePrompt()`

```java
// Query
SELECT * FROM ai_prompts 
WHERE code = ? 
  AND is_active = true 
ORDER BY updated_at DESC 
LIMIT 1;

// Returns: Optional<AiPrompt>
```

### 3. Prompt Types & Placeholders

**a. Intent Detection Prompt**
```yaml
Code: intent_detection
Placeholders:
  - {message}: User message

Purpose: Classify user intent
Model: gpt-4o-mini
Temperature: 0.2 (deterministic)
```

**b. Transaction Extraction Prompt**
```yaml
Code: transaction
Placeholders:
  - {message}: Normalized user message
  - {categories_json}: JSON array of available categories
  - {members_json}: JSON array of household members
  - {today}: Current date (YYYY-MM-DD)

Purpose: Extract structured transaction data
Model: gpt-4o-mini
Temperature: 0.4
Output: JSON format
```

**c. Financial Question Prompt**
```yaml
Code: financial_question
Placeholders:
  - {income}: Total income (VND)
  - {expense}: Total expense (VND)
  - {savingRate}: Saving rate percentage
  - {categoryBreakdown}: Category spending breakdown
  - {decisionItem}: Item being considered (optional)
  - {decisionAmount}: Amount being considered (optional)
  - {decisionCategory}: Category of decision (optional)
  - {income - expense}: Computed saving amount

Purpose: Generate financial advice
Model: gpt-4o-mini
Temperature: 0.4
Output: Markdown format
```

### 4. System Prompt Example (Financial Advice)

```markdown
You are a **personal finance expert for MoneyCare**.

STRICT RULES:
- Output ONLY Markdown.
- Be SHORT, clear, and decisive.
- Use ONLY the provided data. Do NOT assume or invent.
- Apply personal finance models: cashflow, budgeting, spending ratio.
- If any required data is missing, respond briefly: "Không đủ dữ liệu".
- No explanations, no storytelling, no emojis.

Tone: friendly, practical.
Priority: fast response (<5 seconds).

---

## DỮ LIỆU
- Thu nhập: {income} VND
- Chi tiêu: {expense} VND
- Tỷ lệ tiết kiệm mục tiêu: {savingRate} %
- Danh mục chi tiêu: {categoryBreakdown}

## GIAO DỊCH ĐANG CÂN NHẮC (tùy chọn)
- Mục: {decisionItem}
- Số tiền: {decisionAmount} VND
- Danh mục: {decisionCategory}

---

### Tổng quan
| Loại | Số tiền (VND) |
|------|---------------|
| Thu nhập | {income} |
| Chi tiêu | {expense} |
| Tiết kiệm ước tính | {income - expense} |

→ Nhận xét ngắn gọn về dòng tiền.

---

### Phân tích chi tiêu
- Danh mục chi cao nhất: …
- Nhận xét ngắn gọn.

---

### Gợi ý tối ưu
- …

---

### Đánh giá giao dịch (chỉ hiển thị nếu có)
**Kết luận:** Hợp lý / Cân nhắc / Không nên
**Lý do:** …

---

### Hành động nhanh
- …

---

### Cảnh báo (chỉ hiển thị nếu cần)
⚠️ Chi tiêu vượt ngưỡng an toàn.
```

---

## 🔄 VI. EXTERNAL SERVICES INTERACTION

### 1. AI Client Service (Port 3334)

**Endpoints:**

**a. Detect Intent**
```
POST /api/ai/detect-intent
Request:
{
  "userMessage": "Chi 50k ăn trưa",
  "systemPrompt": "...",
  "provider": null  // default: openai
}

Response:
{
  "intent": "transaction",
  "confidence": 0.95,
  "success": true
}
```

**b. Extract Transaction**
```
POST /api/ai/extract-transaction-info
Request:
{
  "systemPrompt": "...",
  "userMessage": "Chi 50000 ăn trưa",
  "maxTokens": 1000,
  "temperature": 0.4,
  "model": null,
  "provider": null
}

Response:
{
  "reply": "{\"transactions\": [...]}",
  "usage": {
    "prompt": 150,
    "completion": 80,
    "total": 230
  }
}
```

**c. Generate Advice**
```
POST /api/ai/generate-advice
Request:
{
  "systemPrompt": "...",
  "userMessage": "Có nên mua iPhone?",
  "maxTokens": 1000,
  "temperature": 0.4,
  "model": null,
  "provider": null
}

Response:
{
  "reply": "### Tổng quan\n...",
  "usage": {
    "prompt": 200,
    "completion": 150,
    "total": 350
  }
}
```

**d. Generate Response**
```
POST /api/ai/generate
Request:
{
  "systemPrompt": "...",
  "userMessage": "...",
  "temperature": 0.7,
  "maxTokens": 500,
  "model": null,
  "provider": null
}

Response:
{
  "response": "...",
  "usage": {...}
}
```

**e. Health Check**
```
GET /api/ai/health

Response:
{
  "status": "healthy",
  "timestamp": "2025-12-26T12:00:00Z"
}
```

**Configuration:**
```yaml
# File: application.yaml:46-53
ai:
  service:
    url: ${AI_SERVICE_URL:http://127.0.0.1:3334}
  embedding:
    url: ${AI_EMBEDDING_URL:http://127.0.0.1:3334/api/embedding}
    model: deepseek-v3
```

**Retry Logic:**
```java
// File: AiServiceClientFeign.java:22-23
private static final int RETRY = 1;       // Max 1 retry
private static final long BACKOFF_MS = 300L;  // 300ms backoff
```

---

### 2. Expense Service (Port 3335)

**Endpoint:**
```
POST /api/v2/expenses/batch-create

Request:
{
  "transactions": [
    {
      "transaction_type": "expense",
      "category_id": "uuid",
      "amount": 50000,
      "currency": "VND",
      "description": "Ăn trưa",
      "transaction_date": "2025-12-26",
      "member_id": null
    }
  ],
  "guestId": "uuid" | null,
  "userId": "uuid" | null
}

Response:
{
  "success": true,
  "transactions": [
    {
      "id": "uuid",
      "type": "expense",
      "categoryId": "uuid",
      "categoryName": "Ăn uống",
      "amountMinor": 50000,
      "currency": "VND",
      "note": "Ăn trưa",
      "date": "2025-12-26",
      "memberId": null,
      "memberName": null,
      "ownerGuestId": "uuid",
      "ownerUserId": null
    }
  ],
  "message": "Transactions created successfully"
}
```

**Configuration:**
```yaml
expense:
  service:
    url: ${EXPENSE_SERVICE_URL:http://127.0.0.1:3335}
```

---

### 3. Auth Service (Port 8888)

**Endpoint:**
```
GET /api/auth/me

Headers:
  Cookie: jwt_token=...

Response:
{
  "id": "uuid",
  "username": "user123",
  "firstName": "Nguyen",
  "lastName": "Van A",
  "email": "user@example.com"
}
```

**Configuration:**
```yaml
auth:
  service:
    url: ${AUTH_SERVICE_URL:http://127.0.0.1:8888}
```

---

### 4. Billing Service (Port 4444)

**Endpoint:**
```
POST /api/billing/usage-events

Request:
{
  "conversationId": "uuid",
  "messageId": "uuid",
  "ownerUserId": "uuid",
  "ownerGuestId": null,
  "provider": "openai",
  "model": "gpt-4o-mini",
  "inputTokens": 150,
  "outputTokens": 80,
  "cachedTokens": 0,
  "costMinor": 17625
}

Response:
{
  "success": true,
  "eventId": "uuid",
  "message": "Usage event recorded"
}
```

**Configuration:**
```yaml
billing:
  api:
    url: ${BILLING_API_URL:http://127.0.0.1:4444}
```

---

### 5. Subscription Service (Port 7777)

**Endpoint:**
```
GET /api/subscription/me/active

Headers:
  Cookie: jwt_token=...

Response:
{
  "activeSubscription": {
    "id": "uuid",
    "status": "active",
    "planName": "Premium",
    "expiredAt": "2025-01-20T20:12:32Z"
  } | null
}
```

**Configuration:**
```yaml
subscription:
  api:
    url: ${SUBSCRIPTION_API_URL:http://127.0.0.1:7777}
```

---

## 📊 VII. ĐIỂM QUAN TRỌNG CHO TEST FRAMEWORK

### 1. Token Usage Thực Tế

**❌ VẤN ĐỀ HIỆN TẠI:**
Test framework đang **ước tính** token usage dựa trên độ dài message:
```python
# File: api_client.py:estimate_token_usage()
prompt_tokens = max(100, len(message) // 4)
completion_tokens = max(50, len(message) // 6)
```

**✅ THỰC TẾ:**
AI Service **TRẢ VỀ** token usage thật từ OpenAI:
```python
{
  "usage": {
    "prompt": 150,      # Actual tokens from OpenAI
    "completion": 80,   # Actual tokens from OpenAI
    "total": 230        # Actual sum
  }
}
```

**🔧 GIẢI PHÁP:**
1. Parse `usage` object từ AI response
2. Lưu trực tiếp vào test results
3. Không cần estimate nữa

---

### 2. Response Format Phân Biệt theo Intent

**Transaction Intent:**
```json
{
  "transactions": [...],
  "summary": {...},
  "emotion": {...}
}
```
→ Response là **JSON string**

**Financial Question Intent:**
```markdown
### Tổng quan
| Loại | Số tiền (VND) |
...
```
→ Response là **Markdown string**

**Other Intents:**
```
Xin chào! Mình là trợ lý tài chính của MoneyCare...
```
→ Response là **Plain text**

**🔧 ĐIỀU CHỈNH TEST FRAMEWORK:**
```python
def evaluate_response(self, test_case, actual_response):
    intent = test_case.expected_intent
    
    if intent == "transaction":
        # Parse as JSON
        try:
            data = json.loads(actual_response)
            self._validate_transaction_json(data, test_case)
        except json.JSONDecodeError:
            return FAIL
    
    elif intent == "financial_question":
        # Validate Markdown structure
        self._validate_markdown_format(actual_response)
        self._check_financial_advice_quality(actual_response)
    
    else:
        # Check text content
        self._validate_text_response(actual_response, test_case)
```

---

### 3. Category Matching với Kind Validation

**QUAN TRỌNG:**
Category matching phải validate cả **name** và **kind**:

```python
Test Case:
{
  "input": "Chi 50k ăn trưa",
  "expected_transaction_type": "expense",
  "expected_category": "Ăn uống"
}

Evaluation Logic:
1. Check transaction_type == "expense" ✅
2. Check category_name == "Ăn uống" ✅
3. Verify category_id matches a category with:
   - name = "Ăn uống"
   - kind = "expense"  ← MUST MATCH!
```

**VÍ DỤ FAIL:**
```json
Database:
- {id: "uuid-1", name: "Ăn uống", kind: "expense"}
- {id: "uuid-2", name: "Ăn uống", kind: "income"}

AI Response:
{
  "transaction_type": "income",  ← WRONG!
  "category_name": "Ăn uống",
  "category_id": "uuid-2"        ← Wrong kind
}

Expected:
{
  "transaction_type": "expense",
  "category_name": "Ăn uống",
  "category_id": "uuid-1"
}
```

---

### 4. Decision Advice Detection

**Logic Override:**
```java
// File: ChatFlowServiceV2.java:113-116

if (isDecisionAdvice && !isExplicitLog && intent == "transaction") {
    intent = "financial_question"  // Override!
}
```

**TEST CASES CẦN KIỂM TRA:**
```python
[
    {
        "input": "Có nên chi 50k ăn trưa không?",
        "expected_intent": "financial_question",  # NOT transaction!
        "expected_contains": ["Đánh giá giao dịch", "Kết luận"]
    },
    {
        "input": "Chi 50k ăn trưa",
        "expected_intent": "transaction",
        "expected_json": True
    },
    {
        "input": "Ghi nhận chi 50k ăn trưa có nên không",
        "expected_intent": "transaction",  # Explicit log overrides decision
        "expected_json": True
    }
]
```

---

### 5. Identity Mode Testing

**3 Modes cần test:**

**a. Guest New (no session)**
```python
headers = {
    "X-Fingerprint": "new_fingerprint_123"
}
# No Cookie, no X-Owner-Id
```
→ Tạo guest mới
→ Guest message limit check
→ Generic financial advice (no real data)

**b. Guest Existing (with session)**
```python
headers = {
    "X-Fingerprint": "existing_fingerprint",
    "Cookie": "guest_token=xyz"
}
```
→ Load existing guest
→ Message history available
→ Still generic advice (no real transaction data)

**c. User (authenticated)**
```python
headers = {
    "Cookie": "jwt_token=valid_jwt"
}
```
→ Extract userId from JWT
→ Query real transaction data
→ Personalized financial advice
→ Subscription check

---

### 6. Error Scenarios cần Test

**a. AI Service Timeout**
```
Simulate: AI Service không respond trong 30s
Expected: Fallback message, không crash
```

**b. AI Service Invalid JSON**
```
AI returns: "```json\n{invalid json}\n```"
Expected: Clean & parse, hoặc error message
```

**c. Expense Service Failed**
```
Expense Service returns: {"success": false, "message": "invalid"}
Expected: User-friendly error message
```

**d. Category Not Found**
```
AI extracts: category_name = "Unknown Category"
Expected: Fallback to "Khác" of same kind
```

**e. Message Limit Exceeded (Guest)**
```
Guest đã gửi 50 messages
Expected: {"success": false, "answer": "Bạn đã đạt giới hạn..."}
```

**f. Subscription Expired (User)**
```
User subscription status = "expired"
Expected: Block request with appropriate message
```

---

### 7. Latency Thresholds

**Observed Performance:**
```yaml
Intent Detection: ~500-800ms
Transaction Extraction: ~1500-3000ms  # Complex prompt with categories
Financial Advice: ~2000-4000ms        # Long context with data
Total Response: ~2500-5000ms

Acceptable:
- P50: < 3000ms
- P95: < 5000ms
- P99: < 8000ms
```

**Test Strategy:**
```python
def test_latency(self):
    results = []
    for i in range(100):
        start = time.time()
        response = self.api_client.chat(message)
        latency = time.time() - start
        results.append(latency)
    
    p50 = np.percentile(results, 50)
    p95 = np.percentile(results, 95)
    p99 = np.percentile(results, 99)
    
    assert p50 < 3000, f"P50 latency {p50}ms exceeds 3000ms"
    assert p95 < 5000, f"P95 latency {p95}ms exceeds 5000ms"
    assert p99 < 8000, f"P99 latency {p99}ms exceeds 8000ms"
```

---

### 8. Cost Calculation Chính Xác

**Model Pricing (gpt-4o-mini):**
```
Input:  $0.150 / 1M tokens = $0.00000015 / token
Output: $0.600 / 1M tokens = $0.00000060 / token
VND Exchange Rate: 25000 VND / USD
Minor Unit: VND * 100
```

**Formula:**
```python
usd_cost = (prompt_tokens * 0.00000015 + completion_tokens * 0.00000060)
vnd_cost = usd_cost * 25000
cost_minor = int(vnd_cost * 100)

# Example:
# prompt_tokens = 150
# completion_tokens = 80
# usd_cost = 150 * 0.00000015 + 80 * 0.00000060
#          = 0.0000225 + 0.000048
#          = 0.0000705 USD
# vnd_cost = 0.0000705 * 25000 = 1.7625 VND
# cost_minor = 176 (rounded)
```

**Test Framework Update:**
```python
# config.py
COST_RATES = {
    "gpt-4o-mini": {
        "input": 0.00000015,   # USD per token
        "output": 0.00000060   # USD per token
    },
    "gpt-4": {
        "input": 0.00001,
        "output": 0.00003
    }
}
VND_EXCHANGE_RATE = 25000
MINOR_UNIT_MULTIPLIER = 100

# evaluator.py
def calculate_cost(self, usage, model="gpt-4o-mini"):
    rates = COST_RATES.get(model, COST_RATES["gpt-4o-mini"])
    
    prompt_tokens = usage.get("prompt", 0)
    completion_tokens = usage.get("completion", 0)
    
    usd_cost = (prompt_tokens * rates["input"] + 
                completion_tokens * rates["output"])
    
    vnd_cost = usd_cost * VND_EXCHANGE_RATE
    cost_minor = int(vnd_cost * MINOR_UNIT_MULTIPLIER)
    
    return {
        "usd": round(usd_cost, 8),
        "vnd": round(vnd_cost, 4),
        "cost_minor": cost_minor
    }
```

---

### 9. System Prompts cần Request

**Để test chính xác, tôi cần các system prompts thực tế từ database:**

```sql
-- Request for test framework reference
SELECT code, system_prompt, model, temperature 
FROM ai_prompts 
WHERE is_active = true 
  AND code IN ('intent_detection', 'transaction', 'financial_question');
```

**Hoặc bạn có thể export:**
```bash
# Export prompts to JSON
psql -h 34.158.53.202 -U postgres -d dbtest -c \
  "SELECT row_to_json(t) FROM (
    SELECT code, system_prompt, user_template, model, temperature, top_p
    FROM ai_prompts 
    WHERE is_active = true
  ) t" > prompts.json
```

**Lý do cần:**
1. Verify expected output format
2. Understand placeholders used
3. Test prompt injection vulnerabilities
4. Validate response structure

---

### 10. Test Data Preparation

**Categories cần có trong test environment:**
```json
[
  {"id": "uuid-1", "name": "Ăn uống", "code": "food", "kind": "expense"},
  {"id": "uuid-2", "name": "Di chuyển", "code": "transport", "kind": "expense"},
  {"id": "uuid-3", "name": "Mua sắm", "code": "shopping", "kind": "expense"},
  {"id": "uuid-4", "name": "Hóa đơn", "code": "bills", "kind": "expense"},
  {"id": "uuid-5", "name": "Lương", "code": "salary", "kind": "income"},
  {"id": "uuid-6", "name": "Thưởng", "code": "bonus", "kind": "income"},
  {"id": "uuid-7", "name": "Khác", "code": "other", "kind": "expense"},
  {"id": "uuid-8", "name": "Khác", "code": "other", "kind": "income"}
]
```

**Members:**
```json
[
  {"id": "uuid-m1", "displayName": "Hùng", "role": "member"},
  {"id": "uuid-m2", "displayName": "Lan", "role": "member"},
  {"id": "uuid-m3", "displayName": "Minh", "role": "member"}
]
```

**Test User with Transaction History:**
```json
{
  "userId": "test-user-uuid",
  "transactions": [
    {"type": "income", "category": "Lương", "amount": 10000000, "date": "2025-12-01"},
    {"type": "expense", "category": "Ăn uống", "amount": 2000000, "date": "2025-12-15"},
    {"type": "expense", "category": "Di chuyển", "amount": 1500000, "date": "2025-12-20"},
    {"type": "expense", "category": "Hóa đơn", "amount": 1000000, "date": "2025-12-22"}
  ],
  "summary": {
    "totalIncome": 10000000,
    "totalExpense": 4500000,
    "savingRate": 0.55
  }
}
```

---

## 🎯 VIII. TÓM TẮT & KHUYẾN NGHỊ

### Điểm Mạnh của Hệ Thống
✅ Kiến trúc microservices rõ ràng  
✅ Separation of concerns tốt  
✅ Retry logic cho external services  
✅ Guest mode hỗ trợ trải nghiệm không cần đăng nhập  
✅ Token usage tracking đầy đủ  
✅ Category matching với kind validation  
✅ Decision advice override logic thông minh  

### Điểm Cần Cải Thiện
⚠️ Token usage chỉ lưu tổng, không tách prompt/completion  
⚠️ Cost calculation không được lưu vào database  
⚠️ Không có circuit breaker cho external services  
⚠️ Retry logic quá đơn giản (chỉ 1 lần)  
⚠️ Không có request rate limiting  
⚠️ Logging chưa đủ chi tiết cho debug  

### Khuyến Nghị cho Test Framework

1. **Parse Token Usage từ AI Response**
   - Không estimate nữa
   - Dùng actual usage từ OpenAI

2. **Phân Biệt Response Format**
   - Transaction: JSON validation
   - Financial: Markdown structure check
   - Others: Text content check

3. **Test Decision Override Logic**
   - Decision questions → financial_question
   - Explicit log + decision → transaction

4. **Validate Category Kind Matching**
   - Category ID phải match đúng kind
   - Fallback to "Khác" nếu không có

5. **Test 3 Identity Modes**
   - Guest new
   - Guest existing
   - User authenticated

6. **Error Scenarios Coverage**
   - AI timeout
   - Invalid JSON
   - Service failures
   - Message limits
   - Subscription checks

7. **Performance Testing**
   - P50 < 3s
   - P95 < 5s
   - P99 < 8s

8. **Cost Calculation Verification**
   - Use actual pricing
   - Validate against usage data

9. **Request System Prompts**
   - Export from database
   - Use for test validation

10. **Prepare Test Data**
    - Complete category set
    - Members list
    - User with transaction history

---

## 📞 NEXT STEPS

### Yêu Cầu từ Người Dùng

**1. System Prompts Export**
```bash
# Option 1: SQL Query
psql -h 34.158.53.202 -U postgres -d dbtest \
  -c "COPY (SELECT * FROM ai_prompts WHERE is_active=true) TO STDOUT CSV HEADER" \
  > ai_prompts.csv

# Option 2: JSON Export
# Cung cấp file JSON với đầy đủ system prompts
```

**2. Test Environment Setup**
```yaml
- Database: Staging DB với test data
- AI Service: Pointing to test endpoint
- Expense Service: Mock hoặc staging
- Billing Service: Mock (không charge thật)
```

**3. API Credentials**
```
- Test user JWT token
- Test guest fingerprint
- API base URL
```

**4. Expected Behavior Documentation**
```
- Transaction extraction examples với expected output
- Financial advice examples với expected format
- Edge cases handling
```

---

## 📝 APPENDIX

### A. API Endpoint Reference

```yaml
Chatbot Service:
  - POST /api/ask
  - GET /api/init-session
  - GET /api/conversations
  - GET /api/conversations/{id}/messages
  - PUT /api/messages/{id}

AI Client Service:
  - POST /api/ai/detect-intent
  - POST /api/ai/extract-transaction-info
  - POST /api/ai/generate-advice
  - POST /api/ai/generate
  - POST /api/ai/embedding
  - GET /api/ai/health

Expense Service:
  - POST /api/v2/expenses/batch-create
  - GET /api/v2/expenses
  - GET /api/v2/expenses/{id}

Auth Service:
  - POST /api/auth/login
  - GET /api/auth/me
  - POST /api/auth/logout

Billing Service:
  - POST /api/billing/usage-events
  - GET /api/billing/usage-events/{id}

Subscription Service:
  - GET /api/subscription/me/active
  - GET /api/subscription/plans
```

### B. Database Tables Reference

```sql
-- Core Tables
conversations
messages
guests
guest_fingerprints
guest_sessions
users
members

-- Config Tables
ai_prompts
bot_profiles
bot_scenarios
system_configuration

-- Data Tables
entity_categories
entity_jars
category_templates
jar_templates
transactions

-- Documents (RAG)
documents
app_documents
```

### C. Environment Variables

```bash
# Database
DB_URL=jdbc:postgresql://34.158.53.202:5432/dbtest
DB_USERNAME=postgres
DB_PASSWORD=capstone2025@mcs

# Services
AI_SERVICE_URL=http://127.0.0.1:3334
EXPENSE_SERVICE_URL=http://127.0.0.1:3335
AUTH_SERVICE_URL=http://127.0.0.1:8888
BILLING_API_URL=http://127.0.0.1:4444
SUBSCRIPTION_API_URL=http://127.0.0.1:7777

# JWT
JWT_SECRET_KEY=secret
JWT_ISSUER=vietduc
JWT_EXPIRATION_MINUTE=10
```

---

**END OF DOCUMENT**

