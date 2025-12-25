# MoneyCare Chatbot Test Framework

Framework kiểm thử chatbot AI theo các tiêu chuẩn:
- **C-L-A-S-S**: Cost, Latency, Accuracy, Scalability, Stability
- **OWASP LLM Top 10**: Security testing cho LLM applications
- **CLASS Design**: Scaffolding, Step-by-step confirmation, Clarification, Feedback

## 📁 Cấu trúc thư mục

```
moneycare-test-framework/
├── config.py              # Cấu hình test
├── models.py              # Data models
├── api_client.py          # API client cho chatbot
├── evaluator.py           # Đánh giá kết quả test
├── test_runner.py         # Chạy test cases
├── report_generator.py    # Tạo báo cáo Excel
├── run_tests.py           # Entry point chính
├── requirements.txt       # Dependencies
├── test_cases.json        # Test cases chức năng
├── test_cases_security.json    # Test cases bảo mật
├── test_cases_classs.json      # Test cases C-L-A-S-S
├── test_cases_class_design.json # Test cases CLASS design
├── test_logs/             # Log từng test run
└── test_results/          # Kết quả và báo cáo
```

## 🚀 Cài đặt

```bash
cd moneycare-test-framework
pip install -r requirements.txt
```

## 📖 Sử dụng

### Chạy tất cả test cases

```bash
python run_tests.py -f test_cases.json
```

### Chạy test security (OWASP)

```bash
python run_tests.py -f test_cases_security.json
```

### Chạy test C-L-A-S-S metrics

```bash
python run_tests.py -f test_cases_classs.json
```

### Chạy test CLASS design principles

```bash
python run_tests.py -f test_cases_class_design.json
```

### Lọc theo feature hoặc priority

```bash
# Chỉ test Security
python run_tests.py -f test_cases_security.json --feature Security

# Chỉ test Critical priority
python run_tests.py -f test_cases_security.json --priority Critical
```

### Cấu hình môi trường

```bash
# Test với URL khác
python run_tests.py -f test_cases.json --url http://staging.example.com:3333

# Test với environment khác
python run_tests.py -f test_cases.json --env Production
```

### Export formats

```bash
# Excel (mặc định)
python run_tests.py -f test_cases.json --export excel

# CSV
python run_tests.py -f test_cases.json --export csv

# JSON
python run_tests.py -f test_cases.json --export json
```

## 📊 Báo cáo Excel

Báo cáo Excel bao gồm các sheet:

| Sheet | Nội dung |
|-------|----------|
| 00_Summary | Tổng quan kết quả test |
| 01_Test_Results | Kết quả từng test case |
| 02_Test_Run_Log | Log chi tiết từng lần chạy |
| 03_Security_Analysis | Phân tích bảo mật |
| 04_OWASP_Matrix | Ma trận OWASP LLM Top 10 |
| 05_CLASS_Checklist | Checklist CLASS design |
| 06_CLASSS_Metrics | Metrics C-L-A-S-S |
| 07_Failed_Tests | Chi tiết test thất bại |

## 📝 Cấu trúc Test Case

```json
{
  "Test_Case_ID": "TC_001",
  "Feature_Area": "Transaction_Parse",
  "Description_VN": "Parse giao dịch chi tiêu đơn giản",
  "User_Message_Input": "chi 50k ăn trưa",
  "Precondition": "Guest/User session active",
  "Expected_Bot_Response": "JSON chứa transaction",
  "Expected_Parsed_Transaction": {
    "transaction_type": "expense",
    "amount": 50000,
    "currency": "VND",
    "category_name": "Ăn uống"
  },
  "Target_Dimensions_CLASSS": ["A", "L"],
  "Target_OWASP_Risks": [],
  "Target_CLASS_Principles": ["Step-by-step_confirmation"],
  "Priority": "High"
}
```

## 🔐 OWASP LLM Top 10 Coverage

| ID | Risk | Test Coverage |
|----|------|---------------|
| LLM01 | Prompt Injection | ✅ SEC_001-005, SEC_020-025 |
| LLM02 | Insecure Output Handling | ✅ SEC_014-016 |
| LLM04 | Model Denial of Service | ✅ SEC_011-013 |
| LLM06 | Sensitive Info Disclosure | ✅ SEC_006-010 |
| LLM08 | Excessive Agency | ✅ SEC_017-019 |
| LLM09 | Overreliance | ✅ SEC_023 |

## 📈 C-L-A-S-S Metrics

- **C (Cost)**: Token usage, estimated cost VND
- **L (Latency)**: Response time ms
- **A (Accuracy)**: Parse accuracy %
- **S (Scalability)**: Concurrent request handling
- **S (Stability)**: Error rate, consistency

## 🎯 CLASS Design Principles

- **Scaffolding**: Bot hướng dẫn từng bước
- **Step-by-step confirmation**: Bot xác nhận trước khi thực hiện
- **Clarification**: Bot hỏi lại khi mơ hồ
- **Feedback**: Bot phản hồi rõ ràng sau action

## 🔧 Tùy chỉnh

### Thêm test case mới

1. Mở file `test_cases_*.json` tương ứng
2. Thêm object test case mới vào array `test_cases`
3. Đảm bảo có đủ các field required

### Thay đổi thresholds

Chỉnh sửa trong `config.py`:

```python
latency_warning_ms: int = 3000
latency_critical_ms: int = 5000
accuracy_pass_threshold: float = 0.8
```

### Thêm security keywords

Chỉnh sửa `SECURITY_KEYWORDS` trong `config.py`

## 📞 Troubleshooting

### Connection refused
- Kiểm tra chatbot service đang chạy
- Kiểm tra URL và port đúng

### Timeout errors
- Tăng `--timeout` parameter
- Kiểm tra network connectivity

### Import errors
- Chạy `pip install -r requirements.txt`
- Kiểm tra Python version >= 3.9
