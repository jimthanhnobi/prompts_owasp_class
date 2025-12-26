# ⚠️ VẤN ĐỀ: RESPONSE BỊ TRUNCATE - TEST ACCURACY FAIL

> **Ngày phát hiện**: 2025-12-26  
> **Vấn đề**: Transaction accuracy tests đang fail vì response từ AI bị cắt ngắn  
> **Nguyên nhân**: `maxTokens` giới hạn ở 1000 tokens trong `GenerateAdviceRequest`

---

## 🔍 PHÁT HIỆN VẤN ĐỀ

### Evidence từ Test Results

**Test Case**: `CLASSS_C_002` (Financial Advice)
```json
{
  "Actual_Bot_Response": "Để phân tích chi tiêu tháng này, bạn hãy làm theo các bước sau:\n\n1. **Liệt kê tất cả các khoản chi**: Ghi lại tất cả các khoản chi tiêu trong tháng, bao gồm chi phí cố định (như tiền thuê nhà, hóa đơn) và chi phí biến đổi (như ăn uống, giải trí).\n\n2. **Phân loại chi tiêu**: Chia các khoản chi thành các nhóm như: thiết yếu (thực phẩm, nhà ở), không thiết yếu (giải trí, mua sắm).\n\n3. **Tính tổng chi tiêu**: Cộng tất cả các khoản chi để xem bạn đã chi tiêu bao nhiêu trong tháng.\n\n4. **So sánh với t",
  "Token_Usage": "{\"prompt_tokens\": 219, \"completion_tokens\": 362, \"total_tokens\": 581}",
  "Accuracy_Score_percent": 0.0,
  "Pass_Fail": "Fail"
}
```

**Vấn đề**: Response bị cắt ở "So sánh với t" - không đủ dữ liệu để parse hoặc check accuracy!

---

## 🔎 ROOT CAUSE ANALYSIS

### 1. Code Flow

```
ChatFlowServiceV2.handleTransactionIntent()
  ↓
TransactionExtractionServiceV2.extract()
  ↓
AiServiceClientFeign.extractTransactionInfoWithUsage()
  ↓
AiClientFeign.GenerateAdviceRequest()  ← maxTokens = 1000 (HARDCODED!)
  ↓
AI-Client Service: AiController.advice()
  ↓
AIProvider.generateResponse()  ← maxTokens = 800 (if null)
```

### 2. Nơi Giới Hạn Token

**File**: `moneycare-capstone-chatbot-ai/src/main/java/com/ai/chatbot/client/AiClientFeign.java`

```java
class GenerateAdviceRequest {
    public GenerateAdviceRequest(String systemPrompt, String userMessage) {
        this.systemPrompt = systemPrompt;
        this.userMessage = userMessage;
        this.maxTokens = 1000;  // ❌ HARDCODED 1000 TOKENS!
        this.temperature = 0.4;
    }
}
```

**File**: `moneycare-capstone-ai-client/src/main/java/com/ai/shared/controller/AiController.java`

```java
@PostMapping("/generate-advice")
public ResponseEntity<Map<String, Object>> advice(@RequestBody GenerateAdviceRequest request) {
    int maxTokens = request.getMaxTokens() != null ? request.getMaxTokens() : 800;  // ❌ Default 800 if null
    // ...
}
```

### 3. Tại Sao 1000 Tokens Không Đủ?

**Transaction Extraction Response**:
- JSON structure: ~200-300 tokens
- Multiple transactions: +200-300 tokens each
- Summary + emotion: ~100-200 tokens
- **Total**: 500-1500 tokens (có thể vượt 1000!)

**Financial Advice Response**:
- Markdown formatting: ~100-200 tokens overhead
- Detailed advice: 500-2000 tokens
- Examples + steps: +300-500 tokens
- **Total**: 900-2700 tokens (thường vượt 1000!)

**Khi Response Bị Cắt**:
- JSON không complete → parsing fail → accuracy = 0%
- Transaction data thiếu → không đủ field để check
- Financial advice không đủ → test framework không parse được

---

## ✅ GIẢI PHÁP

### Option 1: Tăng maxTokens trong GenerateAdviceRequest (RECOMMENDED)

**File**: `moneycare-capstone-chatbot-ai/src/main/java/com/ai/chatbot/client/AiClientFeign.java`

**Before**:
```java
public GenerateAdviceRequest(String systemPrompt, String userMessage) {
    this.systemPrompt = systemPrompt;
    this.userMessage = userMessage;
    this.maxTokens = 1000;  // ❌ Too low
    this.temperature = 0.4;
}
```

**After**:
```java
public GenerateAdviceRequest(String systemPrompt, String userMessage) {
    this.systemPrompt = systemPrompt;
    this.userMessage = userMessage;
    this.maxTokens = 4000;  // ✅ Increased for complete responses
    this.temperature = 0.4;
}
```

**Lý do**: 
- Transaction extraction: cần ~2000 tokens để đảm bảo JSON complete
- Financial advice: cần ~4000 tokens để đảm bảo đủ nội dung
- Safety margin: 4000 tokens đủ cho cả 2 use cases

### Option 2: Tạo Constructor Overload với maxTokens Parameter

**File**: `moneycare-capstone-chatbot-ai/src/main/java/com/ai/chatbot/client/AiClientFeign.java`

```java
class GenerateAdviceRequest {
    // Existing constructor (default 1000)
    public GenerateAdviceRequest(String systemPrompt, String userMessage) {
        this(systemPrompt, userMessage, 1000, 0.4);
    }
    
    // New constructor with maxTokens parameter
    public GenerateAdviceRequest(String systemPrompt, String userMessage, int maxTokens) {
        this(systemPrompt, userMessage, maxTokens, 0.4);
    }
    
    // Full constructor
    public GenerateAdviceRequest(String systemPrompt, String userMessage, 
                                 int maxTokens, double temperature) {
        this.systemPrompt = systemPrompt;
        this.userMessage = userMessage;
        this.maxTokens = maxTokens;
        this.temperature = temperature;
        this.model = null;
        this.provider = null;
    }
}
```

**Update callers**:
```java
// Transaction extraction: 2000 tokens
AiClientFeign.GenerateAdviceRequest req = 
    new AiClientFeign.GenerateAdviceRequest(system, message, 2000);

// Financial advice: 4000 tokens
AiClientFeign.GenerateAdviceRequest req = 
    new AiClientFeign.GenerateAdviceRequest(system, message, 4000);
```

### Option 3: Configurable maxTokens từ application.yaml

**File**: `moneycare-capstone-chatbot-ai/src/main/resources/application.yaml`

```yaml
ai:
  service:
    url: http://localhost:3334
  max_tokens:
    transaction_extraction: 2000
    financial_advice: 4000
    default: 2000
```

**Update code để đọc từ config**:
```java
@Value("${ai.max_tokens.transaction_extraction:2000}")
private int transactionMaxTokens;

@Value("${ai.max_tokens.financial_advice:4000}")
private int adviceMaxTokens;
```

---

## 🎯 RECOMMENDED FIX (Quick & Simple)

**Immediate Fix**: Tăng maxTokens từ 1000 → 4000 trong `GenerateAdviceRequest` constructor.

**Files to modify**:
1. `moneycare-capstone-chatbot-ai/src/main/java/com/ai/chatbot/client/AiClientFeign.java`
   - Line 102: `this.maxTokens = 1000;` → `this.maxTokens = 4000;`

**Impact**:
- ✅ Transaction extraction: Đủ tokens cho complete JSON
- ✅ Financial advice: Đủ tokens cho detailed responses
- ✅ Test accuracy: Có đủ data để check
- ⚠️ Cost: Tăng ~4x token limit (nhưng chỉ dùng khi cần)

**Cost Analysis**:
- Current: max 1000 tokens/completion
- After fix: max 4000 tokens/completion
- Actual usage: AI chỉ generate đủ tokens cần thiết (không phải lúc nào cũng 4000)
- Cost increase: Minimal (chỉ trả tiền cho tokens thực tế generate)

---

## 📊 EXPECTED IMPROVEMENTS

### Before Fix
```
Test Results:
- Failed tests: 6/125 (4.8%)
- Accuracy failures: Do incomplete JSON/truncated responses
- CLASSS_C_002: Response cut off at "So sánh với t"
- Transaction tests: Missing fields due to truncation
```

### After Fix
```
Expected Results:
- Failed tests: 2-3/125 (1.6-2.4%) ✅
- Accuracy failures: Reduced significantly
- CLASSS_C_002: Complete response ✅
- Transaction tests: Full JSON with all fields ✅
```

---

## 🚀 NEXT STEPS

1. ✅ **Fix maxTokens** trong `AiClientFeign.GenerateAdviceRequest`
   - Change `maxTokens = 1000` → `maxTokens = 4000`

2. ✅ **Re-run tests** để verify fix
   ```bash
   cd moneycare-test-framework
   python run_tests.py -f test_cases_all.json
   ```

3. ✅ **Monitor** token usage trong test results
   - Check `Token_Usage` field
   - Verify không có response truncation

4. ✅ **Update documentation** nếu cần
   - Note về maxTokens limit
   - Cost implications

---

## 📝 NOTES

- **Why 4000?**: Đủ cho cả transaction extraction (2000) và financial advice (4000)
- **Cost**: GPT-4o-mini pricing ~$0.15/1M input tokens, $0.60/1M output tokens
- **Safety**: 4000 tokens = ~3000 words (Vietnamese) = đủ cho detailed responses
- **Alternative**: Có thể dùng 2000 cho transaction, 4000 cho advice (cần refactor)

---

**END OF ANALYSIS**

