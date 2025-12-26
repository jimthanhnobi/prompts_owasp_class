# 🎯 TÓM TẮT TEST CASES MỚI

> **Ngày tạo**: 2025-12-26  
> **Mục đích**: Bổ sung test cases dựa trên phân tích system prompts thực tế  
> **Tổng số tests mới**: **47 test cases**

---

## 📊 I. TEST CASES ĐÃ TẠO

### 1. Intent Edge Cases (`test_cases_intent_edge.json`)
**Số lượng**: 15 test cases  
**Mục đích**: Test các edge cases trong intent detection

**Nội dung:**
```yaml
Priority 1 - Unsupported (3 tests):
  - INTENT_EDGE_009: Investment/Chứng khoán
  - INTENT_EDGE_010: Crypto/Bitcoin
  - INTENT_EDGE_011: Investment advice

Priority 4 - Financial Question vs Priority 5 - Transaction (7 tests):
  - INTENT_EDGE_001: "Có nên chi 50k" → financial_question
  - INTENT_EDGE_002: "Muốn mua iPhone" → financial_question
  - INTENT_EDGE_003: "Định chi 100k" → financial_question
  - INTENT_EDGE_004: "Tính mua xe" → financial_question
  - INTENT_EDGE_005: "Đã mua iPhone" → transaction
  - INTENT_EDGE_006: "Vừa chi 50k" → transaction
  - INTENT_EDGE_007: "Chi 100k" → transaction

Special Cases (5 tests):
  - INTENT_EDGE_008: "Ghi nhận chi 50k có nên không" → transaction (explicit log overrides)
  - INTENT_EDGE_012: "Sửa lại" → follow_up
  - INTENT_EDGE_013: "Ý tôi là" → follow_up
  - INTENT_EDGE_014: "Làm sao để" → app_query
  - INTENT_EDGE_015: "Nên tiết kiệm" → financial_question (valid topic)
```

**Key Insights:**
- ✅ Verify intent priority order
- ✅ Test decision questions (có nên, muốn, định) → financial_question
- ✅ Test past actions (đã, vừa) → transaction
- ✅ Test unsupported topics (investment, crypto) → reject
- ✅ Test follow_up và app_query

---

### 2. Amount Parsing (`test_cases_amount_parsing.json`)
**Số lượng**: 20 test cases  
**Mục đích**: Test tất cả các format amount parsing

**Nội dung:**
```yaml
Basic Units (8 tests):
  - AMOUNT_001: 50k = 50,000
  - AMOUNT_002: 100 K = 100,000 (uppercase + space)
  - AMOUNT_003: 100 nghìn = 100,000
  - AMOUNT_004: 50 ngàn = 50,000
  - AMOUNT_005: 3tr = 3,000,000
  - AMOUNT_006: 5m = 5,000,000
  - AMOUNT_007: 2 triệu = 2,000,000
  - AMOUNT_008: 10 củ = 10,000,000

Decimal & Complex (7 tests):
  - AMOUNT_009: 2.5tr = 2,500,000
  - AMOUNT_010: 14tr99 = 14,990,000 ⭐ CRITICAL
  - AMOUNT_011: 19m9 = 19,900,000 ⭐ CRITICAL
  - AMOUNT_012: nửa triệu = 500,000
  - AMOUNT_016: nửa tỷ = 500,000,000
  - AMOUNT_019: 3tr5 = 3,500,000
  - AMOUNT_020: 1.5tr = 1,500,000

Large Units (3 tests):
  - AMOUNT_013: 5 tỏi = 5,000,000,000
  - AMOUNT_014: 2 tỷ = 2,000,000,000
  - AMOUNT_015: 1b = 1,000,000,000

Special Cases (2 tests):
  - AMOUNT_017: 150000 (plain number ≥ 4 digits)
  - AMOUNT_018: Multiple amounts in one message
```

**Parsing Rules:**
```python
k/K               → ×1,000
nghìn/ngàn        → ×1,000
tr/m/triệu/củ     → ×1,000,000
b/tỷ/tỏi          → ×1,000,000,000

Special formats:
14tr99 = 14×1M + 99×10k = 14,990,000
19m9   = 19×1M + 9×100k = 19,900,000
3tr5   = 3×1M + 5×100k  = 3,500,000
```

---

### 3. Member Detection (`test_cases_member_detection.json`)
**Số lượng**: 12 test cases  
**Mục đích**: Test detection của members (Tùng, Trang, Hiền)

**Nội dung:**
```yaml
Basic Detection (3 tests):
  - MEMBER_001: "Chi 50k cho Tùng"
  - MEMBER_002: "Mua quà Trang 200k"
  - MEMBER_003: "Gửi 100k cho Hiền mua sách"

Case-Insensitive (1 test):
  - MEMBER_005: "Chi 50k cho tùng" (lowercase)

No Member (1 test):
  - MEMBER_004: "Chi 100k ăn trưa" → member_id = null

Complex Cases (7 tests):
  - MEMBER_006: Member trong câu dài
  - MEMBER_007: "Cho Trang 100k tiền túi"
  - MEMBER_008: Multiple transactions, one has member
  - MEMBER_009: Income transaction with member
  - MEMBER_010: "Tung" (no dấu) might not match "Tùng"
  - MEMBER_011: Member name at beginning
  - MEMBER_012: All three members in one message
```

**Member IDs:**
```
Tùng:  bd79ba51-8b2b-40aa-8e29-23079f3349bb
Trang: 96f17d8a-f898-4826-b997-1ae8de85ebfe
Hiền:  6d41a461-9757-4cd3-b446-57a7bdd0ed3b
```

---

## 🎯 II. LÝ DO TẠO CÁC TEST CASES NÀY

### 1. Intent Edge Cases
**Vấn đề:** System prompt có intent priority order rõ ràng nhưng chưa có test cases để verify.

**Giải pháp:**
- Test priority order: unsupported > follow_up > app_query > financial_question > transaction
- Test edge case "có nên chi" → financial_question (NOT transaction!)
- Test investment/crypto rejection

**Tác động:**
- ✅ Verify system behavior matches intent priority
- ✅ Prevent false positives (decision questions classified as transaction)
- ✅ Ensure security (investment topics rejected)

---

### 2. Amount Parsing
**Vấn đề:** System prompt có rules phức tạp về amount parsing nhưng không có test coverage.

**Giải pháp:**
- Test tất cả đơn vị: k, tr, m, b, tỷ, tỏi
- Test decimal: 2.5tr
- Test special formats: 14tr99, 19m9, 3tr5
- Test plain numbers

**Tác động:**
- ✅ Verify amount parsing accuracy 100%
- ✅ Catch regressions trong amount conversion
- ✅ Ensure consistency across all formats

**Critical Tests:**
```python
AMOUNT_010: 14tr99 = 14,990,000  # Format Xtr99
AMOUNT_011: 19m9  = 19,900,000   # Format Xm9
AMOUNT_019: 3tr5  = 3,500,000    # Format Xtr{single_digit}
```

---

### 3. Member Detection
**Vấn đề:** Member detection là feature quan trọng nhưng chưa có test coverage.

**Giải pháp:**
- Test detection cho 3 members: Tùng, Trang, Hiền
- Test case-insensitive matching
- Test multiple transactions với members khác nhau
- Test edge cases (no dấu, member at start, income transactions)

**Tác động:**
- ✅ Verify member detection works correctly
- ✅ Test edge cases (position, case, accents)
- ✅ Ensure proper member_id + display_name mapping

---

## 🚀 III. CÁCH SỬ DỤNG

### Option 1: Run từng file riêng lẻ

```bash
# Test intent edge cases
python run_tests.py -f test_cases_intent_edge.json

# Test amount parsing
python run_tests.py -f test_cases_amount_parsing.json

# Test member detection
python run_tests.py -f test_cases_member_detection.json
```

### Option 2: Merge vào test_cases_all.json

```bash
# Merge all new tests vào file all
python merge_test_cases.py

# Run full suite
python run_tests.py -f test_cases_all.json
```

### Option 3: Run selective tests

```python
# Run chỉ critical tests
python run_tests.py -f test_cases_intent_edge.json --priority Critical

# Run chỉ security tests
python run_tests.py -f test_cases_intent_edge.json --category Security
```

---

## 📊 IV. EXPECTED RESULTS

### Test Coverage After Adding New Tests
```yaml
Before: 95 tests
New:    47 tests
Total:  142 tests

By Category:
  - Intent Detection: 25 → 40 (+60%)
  - Amount Parsing:   5 → 25 (+400%)
  - Member Detection: 0 → 12 (NEW!)
  - Security:        25 → 28 (+12%)
  - Functional:      40 → 77 (+92.5%)

By Priority:
  - Critical: 30 → 42 (+40%)
  - High:     40 → 55 (+37.5%)
  - Medium:   20 → 35 (+75%)
  - Low:       5 → 10 (+100%)
```

### Expected Pass Rate
```
Current: 96.8% (93/96)
Target:  98%+ (139/142)

Expected Failures:
  - INTENT_EDGE_009-011: Investment/crypto (should be rejected)
  - MEMBER_010: "Tung" without dấu (depends on implementation)
```

---

## 🔧 V. INTEGRATION WITH EXISTING TESTS

### Files Structure
```
moneycare-test-framework/
├── test_cases_all.json                  ← Original 95 tests
├── test_cases_intent_edge.json          ← NEW: 15 tests
├── test_cases_amount_parsing.json       ← NEW: 20 tests
├── test_cases_member_detection.json     ← NEW: 12 tests
├── system_prompts.json                  ← System prompts reference
├── test_data.json                       ← Members, categories data
├── SYSTEM_INSIGHTS.md                   ← Analysis & findings
└── NEW_TEST_CASES_SUMMARY.md           ← This file
```

### Merge Strategy
```bash
# Automatic merge (recommended)
python merge_test_cases.py --output test_cases_comprehensive.json

# Manual merge
# 1. Open test_cases_all.json
# 2. Copy test_cases array from each new file
# 3. Append to test_cases_all.json
# 4. Update metadata.total_tests
```

---

## ✅ VI. VALIDATION CHECKLIST

Before running tests, verify:

- [ ] System prompts match production (`system_prompts.json`)
- [ ] Test data correct (`test_data.json` - members, categories)
- [ ] API endpoint accessible (`http://127.0.0.1:3333`)
- [ ] Test user/guest has proper setup
- [ ] Members exist in database (Tùng, Trang, Hiền)
- [ ] Categories exist in database (16 categories)

---

## 🎯 VII. SUCCESS CRITERIA

### Must Pass (Critical Tests)
```
INTENT_EDGE_001: Decision question → financial_question ✅
INTENT_EDGE_005: Past action → transaction ✅
INTENT_EDGE_008: Explicit log overrides decision ✅
INTENT_EDGE_009-011: Investment/crypto rejected ✅

AMOUNT_010: 14tr99 = 14,990,000 ✅
AMOUNT_011: 19m9 = 19,900,000 ✅

MEMBER_001-003: Basic member detection ✅
MEMBER_005: Case-insensitive ✅
```

### Should Pass (High Priority)
```
All intent edge cases except unsupported ✅
All amount parsing formats ✅
All member detection cases (except MEMBER_010) ✅
```

### Nice to Have (Medium/Low Priority)
```
MEMBER_010: "Tung" detection (implementation-dependent)
Complex multi-member cases
Edge cases với diacritics
```

---

## 📞 VIII. TROUBLESHOOTING

### If Tests Fail

**Intent Edge Cases:**
```
Issue: "Có nên chi" classified as transaction
Fix: Check intent priority in system prompt
Expected: financial_question (priority 4) > transaction (priority 5)
```

**Amount Parsing:**
```
Issue: 14tr99 ≠ 14,990,000
Fix: Check amount parsing rules in transaction prompt
Formula: 14×1M + 99×10k = 14,990,000
```

**Member Detection:**
```
Issue: Member not detected
Fix: Check members exist in database
Verify: displayName matches exactly (case-insensitive)
```

---

## 🎉 IX. SUMMARY

**Đã tạo:** 47 test cases mới  
**Mục đích:** Verify system behavior với system prompts thực tế  
**Tác động:** 
- ✅ Tăng coverage từ 95 → 142 tests (+49.5%)
- ✅ Test critical edge cases (intent priority, amount formats, member detection)
- ✅ Ensure security (investment/crypto rejection)
- ✅ Improve accuracy validation (amount parsing)

**Next Step:** Run tests và verify expected behaviors! 🚀

---

**END OF SUMMARY**

