# 📋 PHÂN TÍCH KHOẢNG CÁCH YÊU CẦU - HIỆN TRẠNG

## 🎯 YÊU CẦU BAN ĐẦU

### 1. Bổ sung bộ test OWASP Top 10 (để xác minh luận cứ khoa học)
- ✅ **Hiện trạng**: ĐÃ CÓ 30 test cases trong `test_cases_security.json`
- ✅ **Coverage**: 6/10 OWASP LLM Top 10 risks
- ⚠️ **Vấn đề**: Cần tăng số lượng test cases để đảm bảo coverage đầy đủ hơn

### 2. Bổ sung thêm bộ ngưỡng threshold để chứng minh, đánh giá workload
- ✅ **Hiện trạng**: ĐÃ CÓ
  - `workload_thresholds.json` - File chứa tất cả thresholds
  - `WORKLOAD_EVALUATION_GUIDE.md` - Hướng dẫn đánh giá workload
  - Các thresholds chi tiết cho: concurrent users, throughput, latency percentiles, error rate, cost per request

### 3. Tham khảo Framework CLASS để đánh giá
- ✅ **Hiện trạng**: ĐÃ CÓ
  - `test_cases_classs.json` - 40 test cases cho C-L-A-S-S metrics
  - `test_cases_class_design.json` - 12 test cases cho CLASS design principles
  - `CLASS_METRICS_DOCUMENTATION.md` - Tài liệu chi tiết về các chỉ số
- ❌ **Vấn đề LỚN**: Yêu cầu 600-700 test cases, hiện chỉ có **95 test cases**

---

## 📊 HIỆN TRẠNG CHI TIẾT

### Test Cases Summary

| File | Số lượng | Mục đích |
|------|----------|----------|
| `test_cases.json` | 13 | Functional tests |
| `test_cases_security.json` | 30 | OWASP LLM Top 10 |
| `test_cases_classs.json` | 40 | C-L-A-S-S metrics |
| `test_cases_class_design.json` | 12 | CLASS design principles |
| **TỔNG** | **95** | **Thiếu 505-605 test cases** |

### OWASP LLM Top 10 Coverage

| OWASP ID | Risk Name | Test Cases | Status |
|----------|-----------|------------|--------|
| LLM01 | Prompt Injection | SEC_001-005, SEC_020-025 | ✅ 10 tests |
| LLM02 | Insecure Output Handling | SEC_014-016 | ✅ 3 tests |
| LLM04 | Model Denial of Service | SEC_011-013 | ✅ 3 tests |
| LLM06 | Sensitive Info Disclosure | SEC_006-010 | ✅ 5 tests |
| LLM08 | Excessive Agency | SEC_017-019 | ✅ 3 tests |
| LLM09 | Overreliance | SEC_023 | ✅ 1 test |
| LLM03 | Training Data Poisoning | - | ❌ N/A (external API) |
| LLM05 | Supply Chain | - | ❌ N/A (external API) |
| LLM07 | Insecure Plugin Design | - | ❌ N/A (no plugins) |
| LLM10 | Model Theft | - | ❌ N/A (external API) |
| **TỔNG** | | **30 tests** | **Cần thêm 70-100 tests** |

### CLASS Framework Coverage

| Dimension | Test Cases | Hiện trạng | Cần bổ sung |
|-----------|------------|------------|-------------|
| **C** - Cost | CLASSS_C_001-003 (3 tests) | ❌ Không tính được cost thực tế | Cần fix cost calculation + thêm 50-100 tests |
| **L** - Latency | CLASSS_L_001-003 (3 tests) | ✅ OK | Thêm 50-100 tests |
| **A** - Accuracy | CLASSS_A_001-011 (11 tests) | ✅ OK | Thêm 150-200 tests |
| **S1** - Scalability | CLASSS_S1_001-002 (2 tests) | ⚠️ Chưa implement concurrent tests | Thêm 100-150 tests |
| **S2** - Stability | CLASSS_S2_001-005 (5 tests) | ✅ OK | Thêm 50-100 tests |
| **TỔNG** | **40 tests** | | **Cần thêm 400-550 tests** |

### Workload Thresholds

| Threshold Category | Status | Chi tiết |
|-------------------|--------|----------|
| Concurrent Users | ✅ ĐÃ CÓ | 10, 50, 100, 500 users |
| Throughput | ✅ ĐÃ CÓ | Target 50 rps, Min 30 rps |
| Latency Percentiles | ✅ ĐÃ CÓ | P50: 2s, P95: 5s, P99: 8s |
| Error Rate | ✅ ĐÃ CÓ | Max 1%, Warning 0.5% |
| Success Rate | ✅ ĐÃ CÓ | Min 95%, Warning 98% |
| Cost per Request | ✅ ĐÃ CÓ | Simple: <1000 VND, Complex: <5000 VND |
| Token Usage | ✅ ĐÃ CÓ | Simple: 700 tokens, Complex: 2800 tokens |

---

## 🔴 VẤN ĐỀ CHÍNH CẦN FIX

### 1. Cost Calculation không hoạt động ❗❗❗

**Vấn đề**:
- Có function `calculate_cost()` trong `evaluator.py` nhưng không được gọi
- API chatbot không trả về `token_usage` trong response
- `measured_cost_vnd` luôn = 0

**Giải pháp**:
```python
# Option 1: Thêm token usage vào API response
{
  "answer": "...",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 50
  }
}

# Option 2: Estimate tokens từ text length
def estimate_tokens(text: str) -> int:
    # 1 token ≈ 4 characters for English, ≈ 2 characters for Vietnamese
    return len(text) // 3  # Average for mixed content
```

### 2. Thiếu 505-605 test cases ❗❗❗

**Yêu cầu**: 600-700 test cases
**Hiện có**: 95 test cases
**Thiếu**: 505-605 test cases

---

## 🚀 KỂ HOẠCH BỔ SUNG TEST CASES

### Phase 1: Fix Cost Calculation (1-2 ngày)
- [ ] Sửa API để trả về token usage
- [ ] Hoặc implement token estimation
- [ ] Test và verify cost calculation hoạt động

### Phase 2: Bổ sung OWASP Tests (1 tuần - Target: 100 tests)

**LLM01 - Prompt Injection** (thêm 20 tests):
- Direct instruction override
- Context hijacking
- Role-play attacks
- Multi-turn injection
- Indirect prompt injection via data

**LLM02 - Insecure Output** (thêm 15 tests):
- XSS variations
- SQL injection patterns
- Command injection
- Template injection
- Path traversal

**LLM04 - DoS** (thêm 15 tests):
- Very long inputs (1K, 5K, 10K chars)
- Unicode bombs
- Repeated requests
- Memory exhaustion
- CPU-intensive queries

**LLM06 - Info Disclosure** (thêm 20 tests):
- System prompt extraction
- Database info leakage
- API key exposure
- Internal IDs/UUIDs
- User data access

**LLM08 - Excessive Agency** (thêm 20 tests):
- Unauthorized delete
- Unauthorized modify
- Cross-user access
- Privilege escalation
- Batch operations

**LLM09 - Overreliance** (thêm 10 tests):
- Bad financial advice
- Incorrect calculations
- Misleading recommendations

### Phase 3: Bổ sung CLASS Tests (3-4 tuần - Target: 500 tests)

#### **C - Cost** (thêm 80 tests):
- [ ] Transaction parsing variants (30 tests)
  - Chi tiêu đơn giản: 10 variations
  - Thu nhập: 10 variations
  - Chuyển khoản: 10 variations
- [ ] Financial advice (20 tests)
  - Đơn giản: 10 variations
  - Phức tạp: 10 variations
- [ ] Intent detection (20 tests)
- [ ] Error handling (10 tests)

#### **L - Latency** (thêm 80 tests):
- [ ] Simple transactions (30 tests)
- [ ] Complex queries (20 tests)
- [ ] Multi-turn conversations (20 tests)
- [ ] Edge cases (10 tests)

#### **A - Accuracy** (thêm 200 tests):
- [ ] Amount parsing (60 tests)
  - "k" format: 20 variations
  - "triệu" format: 20 variations
  - "trăm", "nghìn": 10 variations
  - Decimal: 10 variations
- [ ] Category mapping (60 tests)
  - Ăn uống: 15 variations
  - Di chuyển: 15 variations
  - Mua sắm: 15 variations
  - Khác: 15 variations
- [ ] Date parsing (40 tests)
  - Relative dates: 20 tests
  - Absolute dates: 20 tests
- [ ] Member/display name (20 tests)
- [ ] Multi-transaction (20 tests)

#### **S1 - Scalability** (thêm 100 tests):
- [ ] Concurrent requests (40 tests)
  - 10 concurrent: 10 variations
  - 50 concurrent: 10 variations
  - 100 concurrent: 10 variations
  - 500 concurrent: 10 variations
- [ ] Sequential load (30 tests)
  - 50 requests: 10 variations
  - 100 requests: 10 variations
  - 500 requests: 10 variations
- [ ] Ramp-up tests (20 tests)
- [ ] Throughput tests (10 tests)

#### **S2 - Stability** (thêm 80 tests):
- [ ] Error handling (30 tests)
  - Invalid input: 10 tests
  - Empty input: 5 tests
  - Special characters: 10 tests
  - Null/None: 5 tests
- [ ] Consistency tests (20 tests)
- [ ] Timeout handling (10 tests)
- [ ] Retry logic (10 tests)
- [ ] Edge cases (10 tests)

### Phase 4: Test Documentation (1 tuần)
- [ ] Ghi note chi tiết cho từng test case
- [ ] Giải thích rõ ràng vấn đề
- [ ] Document expected vs actual
- [ ] Nộp đủ bộ data

---

## 📈 TIMELINE ĐỀ XUẤT

| Phase | Duration | Deliverables | Test Cases |
|-------|----------|--------------|------------|
| **Phase 1** | 1-2 ngày | Fix cost calculation | 0 |
| **Phase 2** | 1 tuần | OWASP tests | +100 (Total: 130) |
| **Phase 3.1** | 1 tuần | C-L-A metrics tests | +160 (Total: 290) |
| **Phase 3.2** | 1 tuần | Accuracy tests | +200 (Total: 490) |
| **Phase 3.3** | 1 tuần | S1-S2 tests | +180 (Total: 670) |
| **Phase 4** | 1 tuần | Documentation | 0 (Total: 670) |
| **TỔNG** | **5-6 tuần** | **Complete test suite** | **670 test cases** |

---

## 🎯 MỤC TIÊU CUỐI CÙNG

### Test Cases Distribution (Target: 670 tests)

| Category | Current | Target | To Add |
|----------|---------|--------|--------|
| Functional | 13 | 30 | +17 |
| OWASP Security | 30 | 130 | +100 |
| Cost (C) | 3 | 83 | +80 |
| Latency (L) | 3 | 83 | +80 |
| Accuracy (A) | 11 | 211 | +200 |
| Scalability (S1) | 2 | 102 | +100 |
| Stability (S2) | 5 | 85 | +80 |
| CLASS Design | 12 | 30 | +18 |
| **TỔNG** | **95** | **670** | **+575** |

### Coverage Goals

- ✅ **OWASP**: 100+ tests covering 6/10 risks với nhiều variations
- ✅ **CLASS**: 500+ tests covering tất cả 5 dimensions
- ✅ **Workload**: Thresholds đầy đủ với 4 levels (Light, Medium, Heavy, Extreme)
- ✅ **Documentation**: Ghi note chi tiết, giải thích rõ ràng từng test case
- ✅ **Data**: Nộp đủ bộ data với kết quả chi tiết

---

## 📝 NOTES CHO TỪNG TEST CASE

Mỗi test case cần có:

```json
{
  "Test_Case_ID": "CLASSS_A_012",
  "Feature_Area": "Accuracy",
  "Description_VN": "Parse số tiền với format '50 nghìn'",
  "User_Message_Input": "chi 50 nghìn ăn sáng",
  "Expected_Parsed_Transaction": {
    "transaction_type": "expense",
    "amount": 50000,
    "category_name": "Ăn uống"
  },
  "Target_Dimensions_CLASSS": ["A"],
  "Priority": "High",
  
  // NOTES CHI TIẾT
  "Test_Rationale": "Kiểm tra khả năng parse số tiền với từ 'nghìn' thay vì 'k' hoặc 'triệu'",
  "Expected_Behavior": "Bot phải nhận diện '50 nghìn' = 50,000 VND",
  "Metrics_Evaluated": {
    "accuracy_score": "100% nếu amount = 50000",
    "critical_fields": ["transaction_type", "amount"],
    "flexible_fields": ["category_name"]
  },
  "Pass_Criteria": "amount = 50000 AND transaction_type = 'expense'",
  "Fail_Criteria": "amount != 50000 hoặc không parse được",
  "Edge_Cases_Covered": [
    "Từ 'nghìn' thay vì 'k'",
    "Có khoảng trắng giữa số và đơn vị"
  ],
  "Related_Test_Cases": ["CLASSS_A_001", "CLASSS_A_002"],
  "Business_Impact": "High - User thường dùng 'nghìn' trong giao tiếp hàng ngày"
}
```

---

*Created: 2025-12-26*
*Framework Version: 2.0.0 (Planned)*

