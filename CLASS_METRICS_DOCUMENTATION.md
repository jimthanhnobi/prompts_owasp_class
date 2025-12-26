# 📊 CLASS Framework Metrics Documentation

Tài liệu chi tiết về các chỉ số đánh giá trong CLASS Framework cho MoneyCare Chatbot.

---

## 🎯 Tổng quan CLASS Framework

CLASS Framework đánh giá hiệu năng LLM application theo 5 dimensions:

- **C** - **Cost**: Chi phí vận hành (token usage, API cost)
- **L** - **Latency**: Thời gian phản hồi
- **A** - **Accuracy**: Độ chính xác parsing và intent detection
- **S1** - **Scalability**: Khả năng xử lý tải cao (concurrent requests)
- **S2** - **Stability**: Độ ổn định, xử lý lỗi, tính nhất quán

---

## 💰 C - COST (Chi phí)

### Mô tả
Đo lường chi phí vận hành chatbot, chủ yếu dựa trên token usage của LLM API.

### Cách tính

#### 1. Token Usage
- **Input Tokens**: Số token trong prompt gửi đến LLM
- **Output Tokens**: Số token trong response từ LLM
- **Total Tokens**: Input + Output

#### 2. Cost Calculation (GPT-4o-mini)
```python
# Pricing (USD per 1K tokens)
input_token_rate = 0.00015   # $0.15 per 1M input tokens
output_token_rate = 0.0006  # $0.60 per 1M output tokens

# Cost per request (USD)
cost_usd = (input_tokens / 1000 * input_token_rate) + 
           (output_tokens / 1000 * output_token_rate)

# Convert to VND
cost_vnd = cost_usd * usd_to_vnd_rate  # usd_to_vnd_rate = 24500
```

### Metrics được đo

| Metric | Mô tả | Unit | Threshold |
|--------|-------|------|-----------|
| `prompt_tokens` | Số token trong input prompt | tokens | - |
| `completion_tokens` | Số token trong output response | tokens | - |
| `total_tokens` | Tổng số token | tokens | - |
| `cost_vnd` | Chi phí tính bằng VND | VND | < 1000 VND/request (simple), < 5000 VND/request (complex) |

### Test Cases

#### Simple Transaction (CLASSS_C_001)
- **Input**: "chi 50k ăn trưa"
- **Expected**: 
  - `max_prompt_tokens`: 500
  - `max_completion_tokens`: 200
  - `max_total_tokens`: 700
  - `max_cost_vnd`: ~350 VND

#### Complex Financial Advice (CLASSS_C_002)
- **Input**: "Phân tích chi tiêu tháng này và đưa ra lời khuyên tiết kiệm"
- **Expected**:
  - `max_prompt_tokens`: 2000
  - `max_completion_tokens`: 800
  - `max_total_tokens`: 2800
  - `max_cost_vnd`: ~1400 VND

#### Greeting (CLASSS_C_003)
- **Input**: "Xin chào"
- **Expected**:
  - `max_total_tokens`: 100 (should use template, minimal AI call)
  - `max_cost_vnd`: ~50 VND

### Đánh giá

- ✅ **Pass**: Cost < threshold cho loại request
- ⚠️ **Warning**: Cost > threshold nhưng < 2x threshold
- ❌ **Fail**: Cost > 2x threshold

### Notes

- Cost phụ thuộc vào:
  - Độ dài prompt (context, conversation history)
  - Độ phức tạp của response
  - Model được sử dụng (gpt-4o-mini vs gpt-4o)
- Nên optimize:
  - Giảm context không cần thiết
  - Sử dụng template cho greeting/simple responses
  - Cache responses khi có thể

---

## ⏱️ L - LATENCY (Thời gian phản hồi)

### Mô tả
Đo thời gian từ khi gửi request đến khi nhận được response hoàn chỉnh.

### Cách đo

```python
start_time = time.time()
response = api_client.ask(message)
end_time = time.time()
latency_ms = (end_time - start_time) * 1000
```

### Metrics được đo

| Metric | Mô tả | Unit | Threshold |
|--------|-------|------|-----------|
| `latency_ms` | Thời gian phản hồi | milliseconds | < 3000ms (simple), < 5000ms (complex) |
| `p50_latency_ms` | Median latency (50th percentile) | milliseconds | < 2000ms |
| `p95_latency_ms` | 95th percentile latency | milliseconds | < 5000ms |
| `p99_latency_ms` | 99th percentile latency | milliseconds | < 8000ms |

### Test Cases

#### Simple Transaction Parse (CLASSS_L_001)
- **Input**: "chi 100k cà phê"
- **Expected**:
  - `max_latency_ms`: 3000ms
  - `target_latency_ms`: 2000ms

#### Intent Detection (CLASSS_L_002)
- **Input**: "Tôi muốn ghi chi tiêu"
- **Expected**:
  - `max_latency_ms`: 2000ms
  - `target_latency_ms`: 1000ms

#### Complex Financial Advice (CLASSS_L_003)
- **Input**: "Tháng này tôi chi tiêu có hợp lý không?"
- **Expected**:
  - `max_latency_ms`: 5000ms
  - `target_latency_ms`: 3000ms

### Đánh giá

- ✅ **Pass**: Latency < target
- ⚠️ **Warning**: Latency >= target và < max
- ❌ **Fail**: Latency >= max

### Percentiles

Khi test với nhiều requests, tính percentiles:

```python
latencies = [1500, 1800, 2000, 2200, 2500, 3000, 3500, ...]
p50 = percentile(latencies, 50)  # Median
p95 = percentile(latencies, 95)    # 95% requests < p95
p99 = percentile(latencies, 99)    # 99% requests < p99
```

### Notes

- Latency phụ thuộc vào:
  - Network latency
  - LLM API response time
  - Database query time (nếu có)
  - Processing time
- Nên optimize:
  - Cache frequent responses
  - Parallel processing khi có thể
  - Optimize database queries
  - Use faster models cho simple tasks

---

## 🎯 A - ACCURACY (Độ chính xác)

### Mô tả
Đo độ chính xác của việc parse transaction và detect intent từ user message.

### Cách tính

#### 1. Transaction Parsing Accuracy

```python
def calculate_accuracy(expected, actual):
    correct_fields = 0
    total_fields = 0
    
    for field in expected_fields:
        total_fields += 1
        if field in actual and actual[field] == expected[field]:
            correct_fields += 1
    
    accuracy = (correct_fields / total_fields) * 100
    return accuracy
```

#### 2. Intent Detection Accuracy

```python
if expected_intent == actual_intent:
    accuracy = 100
else:
    accuracy = 0
```

### Metrics được đo

| Metric | Mô tả | Unit | Threshold |
|--------|-------|------|-----------|
| `accuracy_score_percent` | Độ chính xác tổng thể | % | >= 80% |
| `amount_accuracy` | Độ chính xác parse amount | % | >= 95% |
| `category_accuracy` | Độ chính xác parse category | % | >= 85% |
| `type_accuracy` | Độ chính xác detect transaction type | % | >= 90% |
| `date_accuracy` | Độ chính xác parse date | % | >= 80% |
| `intent_accuracy` | Độ chính xác detect intent | % | >= 90% |

### Test Cases

#### Amount Parsing với "k" (CLASSS_A_001)
- **Input**: "chi 50k"
- **Expected**: `amount = 50000`
- **Accuracy Field**: `amount`

#### Amount Parsing với "triệu" (CLASSS_A_002)
- **Input**: "nhận 5 triệu"
- **Expected**: `amount = 5000000`
- **Accuracy Field**: `amount`

#### Amount Parsing với decimal (CLASSS_A_003)
- **Input**: "chi 1.5tr"
- **Expected**: `amount = 1500000`
- **Accuracy Field**: `amount`

#### Transaction Type Detection (CLASSS_A_004, A_005)
- **Input**: "mua sách 200k" → Expected: `transaction_type = "expense"`
- **Input**: "được thưởng 2 triệu" → Expected: `transaction_type = "income"`

#### Category Mapping (CLASSS_A_006, A_007)
- **Input**: "chi 50k ăn phở" → Expected: `category_name = "Ăn uống"`
- **Input**: "đổ xăng 100k" → Expected: `category_name = "Di chuyển"`

#### Date Parsing (CLASSS_A_008, A_009)
- **Input**: "hôm nay chi 50k" → Expected: `transaction_date = "today"`
- **Input**: "hôm qua chi 50k" → Expected: `transaction_date = "yesterday"`

#### Intent Detection (CLASSS_A_010, A_011)
- **Input**: "ghi nhận chi 50k" → Expected: `intent = "transaction"`
- **Input**: "có nên mua điện thoại 10 triệu không?" → Expected: `intent = "financial_question"`

### Đánh giá

- ✅ **Pass**: Accuracy >= 80%
- ⚠️ **Partial**: Accuracy >= 60% và < 80%
- ❌ **Fail**: Accuracy < 60%

### Field-level Accuracy

Một số fields quan trọng hơn:
- `amount`: Critical (phải >= 95%)
- `transaction_type`: High (phải >= 90%)
- `category_name`: Medium (phải >= 85%)
- `transaction_date`: Low (>= 80% acceptable)

### Notes

- Accuracy phụ thuộc vào:
  - Chất lượng LLM model
  - Prompt engineering
  - Context và conversation history
  - Ambiguity trong user message
- Nên improve:
  - Fine-tune prompts
  - Add validation rules
  - Use better models cho critical tasks
  - Provide examples trong prompt

---

## 📈 S1 - SCALABILITY (Khả năng mở rộng)

### Mô tả
Đo khả năng xử lý nhiều requests đồng thời và tải cao.

### Cách test

#### 1. Concurrent Requests Test

```python
async def test_concurrent_requests(num_requests=10):
    tasks = []
    for i in range(num_requests):
        task = asyncio.create_task(send_request(f"chi {i*10}k"))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return analyze_results(results)
```

#### 2. Sequential Load Test

```python
def test_sequential_load(num_requests=50):
    results = []
    for i in range(num_requests):
        result = send_request(f"chi {random.randint(10, 100)}k")
        results.append(result)
    return analyze_results(results)
```

### Metrics được đo

| Metric | Mô tả | Unit | Threshold |
|--------|-------|------|-----------|
| `concurrent_requests` | Số requests đồng thời | count | 10, 50, 100, 500 |
| `throughput_rps` | Requests per second | rps | >= 50 rps |
| `avg_latency_ms` | Average latency | ms | < 5000ms |
| `p95_latency_ms` | 95th percentile latency | ms | < 8000ms |
| `success_rate` | Tỷ lệ thành công | % | >= 95% |
| `error_rate` | Tỷ lệ lỗi | % | < 5% |

### Test Cases

#### 10 Concurrent Requests (CLASSS_S1_001)
- **Input**: 10 concurrent requests với message "chi 50k test"
- **Expected**:
  - `concurrent_requests`: 10
  - `max_avg_latency_ms`: 5000
  - `success_rate_min`: 0.95 (95%)

#### 50 Sequential Requests (CLASSS_S1_002)
- **Input**: 50 sequential requests
- **Expected**:
  - `total_requests`: 50
  - `success_rate_min`: 0.98 (98%)

### Đánh giá

- ✅ **Pass**: 
  - Success rate >= 95%
  - Avg latency < threshold
  - No crashes
- ⚠️ **Warning**:
  - Success rate >= 90% và < 95%
  - Latency tăng nhưng vẫn acceptable
- ❌ **Fail**:
  - Success rate < 90%
  - Latency quá cao
  - Crashes hoặc timeouts

### Workload Levels

| Level | Concurrent Users | Expected Throughput | Max Latency |
|-------|------------------|---------------------|-------------|
| Light | 10 | 10 rps | 3000ms |
| Medium | 50 | 30 rps | 5000ms |
| Heavy | 100 | 50 rps | 8000ms |
| Extreme | 500 | 100 rps | 10000ms |

### Notes

- Scalability phụ thuộc vào:
  - Server resources (CPU, RAM, network)
  - Database performance
  - LLM API rate limits
  - Architecture (single-threaded vs async)
- Nên optimize:
  - Use async/await
  - Implement connection pooling
  - Add caching
  - Use load balancer
  - Optimize database queries

---

## 🛡️ S2 - STABILITY (Độ ổn định)

### Mô tả
Đo khả năng xử lý lỗi, edge cases, và tính nhất quán của responses.

### Cách test

#### 1. Error Handling Test

```python
def test_error_handling():
    invalid_inputs = [
        "",  # Empty
        "chi abc triệu",  # Invalid amount
        "chi 50k @#$%^&*()",  # Special characters
        None,  # Null
    ]
    
    for input in invalid_inputs:
        result = send_request(input)
        assert result.no_crash == True
        assert result.meaningful_response == True
```

#### 2. Consistency Test

```python
def test_consistency():
    message = "chi 50k ăn trưa"
    results = []
    
    for i in range(5):
        result = send_request(message)
        results.append(result)
    
    # Check consistency
    assert all(r.amount == results[0].amount for r in results)
    assert all(r.category == results[0].category for r in results)
```

### Metrics được đo

| Metric | Mô tả | Unit | Threshold |
|--------|-------|------|-----------|
| `no_crash` | Không crash | boolean | True |
| `meaningful_response` | Response có ý nghĩa | boolean | True |
| `response_structure_consistent` | Cấu trúc response nhất quán | boolean | True |
| `amount_consistent` | Amount parse nhất quán | boolean | True |
| `error_rate` | Tỷ lệ lỗi | % | < 1% |
| `timeout_handled` | Xử lý timeout đúng cách | boolean | True |

### Test Cases

#### Invalid JSON Handling (CLASSS_S2_001)
- **Input**: "chi abc triệu"
- **Expected**:
  - `no_crash`: True
  - `meaningful_response`: True (graceful error hoặc clarification request)

#### Empty Message (CLASSS_S2_002)
- **Input**: ""
- **Expected**:
  - `no_crash`: True
  - Graceful handling

#### Special Characters (CLASSS_S2_003)
- **Input**: "chi 50k @#$%^&*()"
- **Expected**:
  - `no_crash`: True
  - Parse transaction hoặc graceful handling

#### Consistency (CLASSS_S2_004)
- **Input**: "chi 50k ăn trưa" (run 5 times)
- **Expected**:
  - `response_structure_consistent`: True
  - `amount_consistent`: True

#### Timeout Handling (CLASSS_S2_005)
- **Input**: "chi 50k test timeout" (simulate slow AI service)
- **Expected**:
  - `no_hang`: True
  - `timeout_handled`: True

### Đánh giá

- ✅ **Pass**: 
  - No crashes
  - Meaningful responses
  - Consistent behavior
  - Error rate < 1%
- ⚠️ **Warning**:
  - Minor inconsistencies
  - Error rate >= 1% và < 5%
- ❌ **Fail**:
  - Crashes
  - No meaningful responses
  - High inconsistency
  - Error rate >= 5%

### Error Types

| Error Type | Expected Behavior |
|------------|------------------|
| Invalid input | Clarification request hoặc error message |
| Empty input | Greeting hoặc clarification |
| Timeout | Timeout message hoặc retry |
| Network error | Error message, không crash |
| API error | Graceful degradation |

### Notes

- Stability phụ thuộc vào:
  - Error handling code
  - Input validation
  - Retry logic
  - Timeout handling
  - LLM model consistency
- Nên improve:
  - Add comprehensive error handling
  - Validate all inputs
  - Implement retry với exponential backoff
  - Add circuit breaker
  - Log errors for debugging

---

## 📊 Tổng hợp đánh giá

### Scoring System

Mỗi dimension được đánh giá theo thang điểm:

| Score | Meaning | Color |
|-------|---------|-------|
| 90-100 | Excellent | 🟢 Green |
| 70-89 | Good | 🟡 Yellow |
| 50-69 | Fair | 🟠 Orange |
| 0-49 | Poor | 🔴 Red |

### Overall CLASS Score

```python
overall_score = (
    cost_score * 0.2 +      # 20% weight
    latency_score * 0.2 +   # 20% weight
    accuracy_score * 0.3 +  # 30% weight (most important)
    scalability_score * 0.15 +  # 15% weight
    stability_score * 0.15      # 15% weight
)
```

### Report Format

Trong Excel report, mỗi test case sẽ có:
- **Actual Metrics**: Giá trị thực tế đo được
- **Expected Metrics**: Giá trị mong đợi
- **Threshold**: Ngưỡng chấp nhận được
- **Status**: Pass/Warning/Fail
- **Notes**: Giải thích chi tiết

---

## 📝 References

- [CLASS Framework Paper](https://arxiv.org/abs/2308.03262)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [GPT-4o-mini Pricing](https://openai.com/api/pricing/)

---

*Last updated: 2025-12-25*
*Framework Version: 1.1.0*

