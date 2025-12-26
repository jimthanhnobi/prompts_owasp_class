# 🚀 Quick Start - Chạy Test Tất Cả

## Cách 1: Chạy tất cả test cases (Recommended)

### Windows:
```bash
run_all_comprehensive.bat
```

### Linux/Mac hoặc Python trực tiếp:
```bash
# Bước 1: Merge tất cả test cases
python merge_test_cases.py

# Bước 2: Chạy tất cả tests và tạo reports
python run_all_tests_comprehensive.py
```

## Cách 2: Chạy với run_tests.py (đã tự động tạo cả JSON + Excel)

```bash
# Merge test cases trước
python merge_test_cases.py

# Chạy với file đã merge
python run_tests.py -f test_cases_all.json
```

## Kết quả

Sau khi chạy, bạn sẽ có:

1. **JSON Report**: `test_results/test_run_YYYYMMDD_HHMMSS.json`
   - Chứa tất cả kết quả test chi tiết
   - Có thể dùng để phân tích sau

2. **Excel Report**: `test_results/test_report_YYYYMMDD_HHMMSS.xlsx`
   - 8 sheets:
     - 00_Framework_Overview
     - 01_Test_Results
     - 02_Metrics_C_L_A_S_S
     - 03_OWASP_Coverage
     - 04_CLASS_Checklist
     - 05_CLASS_Metrics_Explanation (NEW)
     - 06_Thresholds_Comparison (NEW)
     - 07_Workload_Analysis (NEW)

## Tùy chọn

### Chạy với filter:
```bash
# Chỉ test Security
python run_all_tests_comprehensive.py --feature Security

# Chỉ test Critical priority
python run_all_tests_comprehensive.py --priority Critical

# Custom URL
python run_all_tests_comprehensive.py --url http://staging.example.com:3333
```

### Skip merge (dùng file đã có):
```bash
python run_all_tests_comprehensive.py --skip-merge
```

## Tổng số test cases

Hiện tại có **95 test cases** được merge:
- Functional: 13 tests
- Security: 30 tests  
- C-L-A-S-S: 40 tests
- CLASS_Design: 12 tests

---

*Last updated: 2025-12-26*

