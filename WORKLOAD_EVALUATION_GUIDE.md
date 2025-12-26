# 📈 Workload Evaluation Guide

Hướng dẫn đánh giá workload và scalability của MoneyCare Chatbot.

---

## 🎯 Mục tiêu

Đánh giá khả năng của hệ thống xử lý:
- **Concurrent requests**: Nhiều users đồng thời
- **Throughput**: Số requests per second
- **Latency**: Thời gian phản hồi ở các mức tải khác nhau
- **Error rate**: Tỷ lệ lỗi khi tải cao
- **Stability**: Độ ổn định khi tải tăng

---

## 📊 Workload Levels

### Light Load (10 concurrent users)
- **Mô tả**: Normal usage, typical daily traffic
- **Concurrent Users**: 10
- **Expected Throughput**: 10 rps
- **Max Latency**: 3000ms
- **Use Case**: Baseline performance

### Medium Load (50 concurrent users)
- **Mô tả**: Peak hours, increased traffic
- **Concurrent Users**: 50
- **Expected Throughput**: 30 rps
- **Max Latency**: 5000ms
- **Use Case**: Peak hour performance

### Heavy Load (100 concurrent users)
- **Mô tả**: High traffic, promotional events
- **Concurrent Users**: 100
- **Expected Throughput**: 50 rps
- **Max Latency**: 8000ms
- **Use Case**: High traffic scenarios

### Extreme Load (500 concurrent users)
- **Mô tả**: Stress test, maximum capacity
- **Concurrent Users**: 500
- **Expected Throughput**: 100 rps
- **Max Latency**: 10000ms
- **Use Case**: Breaking point test

---

## 🧪 Cách chạy Workload Tests

### 1. Concurrent Requests Test

Test với nhiều requests đồng thời:

```python
# test_workload_concurrent.py
import asyncio
from api_client import MoneyCareAPIClient
from config import TestConfig

async def test_concurrent_requests(num_users=10):
    config = TestConfig()
    results = []
    
    async def send_request(user_id):
        client = MoneyCareAPIClient(config)
        client.init_session()
        response = client.ask(f"chi {user_id * 10}k test")
        return {
            "user_id": user_id,
            "latency_ms": response.latency_ms,
            "success": response.success,
            "error": response.error
        }
    
    tasks = [send_request(i) for i in range(num_users)]
    results = await asyncio.gather(*tasks)
    
    return analyze_results(results)

def analyze_results(results):
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    latencies = [r["latency_ms"] for r in results if r["success"]]
    
    return {
        "total_requests": total,
        "successful_requests": successful,
        "success_rate": successful / total,
        "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
        "p50_latency_ms": percentile(latencies, 50),
        "p95_latency_ms": percentile(latencies, 95),
        "p99_latency_ms": percentile(latencies, 99),
        "error_rate": (total - successful) / total
    }
```

### 2. Sequential Load Test

Test với nhiều requests tuần tự:

```python
# test_workload_sequential.py
import time
from api_client import MoneyCareAPIClient
from config import TestConfig

def test_sequential_load(num_requests=50):
    config = TestConfig()
    client = MoneyCareAPIClient(config)
    client.init_session()
    
    results = []
    start_time = time.time()
    
    for i in range(num_requests):
        response = client.ask(f"chi {i * 10}k test")
        results.append({
            "request_id": i,
            "latency_ms": response.latency_ms,
            "success": response.success,
            "error": response.error
        })
    
    end_time = time.time()
    duration_seconds = end_time - start_time
    throughput_rps = num_requests / duration_seconds
    
    return {
        "total_requests": num_requests,
        "duration_seconds": duration_seconds,
        "throughput_rps": throughput_rps,
        "results": results,
        **analyze_results(results)
    }
```

### 3. Ramp-up Test

Test với tải tăng dần:

```python
# test_workload_rampup.py
async def test_rampup(max_users=100, rampup_steps=10):
    """
    Tăng dần số concurrent users từ 1 đến max_users
    """
    step_size = max_users // rampup_steps
    all_results = []
    
    for num_users in range(step_size, max_users + 1, step_size):
        print(f"Testing with {num_users} concurrent users...")
        results = await test_concurrent_requests(num_users)
        results["concurrent_users"] = num_users
        all_results.append(results)
        
        # Wait between steps
        await asyncio.sleep(5)
    
    return all_results
```

---

## 📈 Metrics cần đo

### 1. Throughput (Requests per Second)

```python
throughput_rps = total_requests / duration_seconds
```

**Thresholds:**
- ✅ **Pass**: >= 50 rps
- ⚠️ **Warning**: >= 30 rps và < 50 rps
- ❌ **Fail**: < 30 rps

### 2. Latency Percentiles

```python
# Sort latencies
latencies_sorted = sorted(latencies)

# Calculate percentiles
p50 = latencies_sorted[int(len(latencies_sorted) * 0.50)]
p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)]
p99 = latencies_sorted[int(len(latencies_sorted) * 0.99)]
```

**Thresholds:**
- **P50 (Median)**: < 2000ms
- **P95**: < 5000ms
- **P99**: < 8000ms

### 3. Success Rate

```python
success_rate = successful_requests / total_requests
```

**Thresholds:**
- ✅ **Pass**: >= 95%
- ⚠️ **Warning**: >= 90% và < 95%
- ❌ **Fail**: < 90%

### 4. Error Rate

```python
error_rate = failed_requests / total_requests
```

**Thresholds:**
- ✅ **Pass**: < 1%
- ⚠️ **Warning**: >= 0.5% và < 1%
- ❌ **Fail**: >= 1%

### 5. Cost per Request

```python
avg_cost_vnd = total_cost_vnd / total_requests
```

**Thresholds:**
- **Simple transaction**: < 1000 VND
- **Complex query**: < 5000 VND

---

## 📊 Đọc kết quả

### Example Output

```json
{
  "workload_level": "heavy",
  "concurrent_users": 100,
  "total_requests": 100,
  "successful_requests": 97,
  "failed_requests": 3,
  "success_rate": 0.97,
  "error_rate": 0.03,
  "throughput_rps": 45.5,
  "latency": {
    "avg_ms": 3200,
    "p50_ms": 2800,
    "p95_ms": 5200,
    "p99_ms": 7500,
    "min_ms": 1500,
    "max_ms": 8500
  },
  "cost": {
    "total_vnd": 97000,
    "avg_per_request_vnd": 970
  },
  "status": "warning",
  "notes": "Error rate slightly above threshold (3% > 1%)"
}
```

### Status Evaluation

```python
def evaluate_workload_status(results):
    status = "pass"
    issues = []
    
    # Check success rate
    if results["success_rate"] < 0.95:
        status = "fail"
        issues.append(f"Success rate too low: {results['success_rate']*100:.1f}%")
    elif results["success_rate"] < 0.98:
        status = "warning"
        issues.append(f"Success rate below warning threshold: {results['success_rate']*100:.1f}%")
    
    # Check error rate
    if results["error_rate"] >= 0.01:
        status = "fail"
        issues.append(f"Error rate too high: {results['error_rate']*100:.1f}%")
    elif results["error_rate"] >= 0.005:
        if status == "pass":
            status = "warning"
        issues.append(f"Error rate above warning: {results['error_rate']*100:.1f}%")
    
    # Check latency
    if results["latency"]["p95_ms"] >= 8000:
        status = "fail"
        issues.append(f"P95 latency too high: {results['latency']['p95_ms']}ms")
    elif results["latency"]["p95_ms"] >= 5000:
        if status == "pass":
            status = "warning"
        issues.append(f"P95 latency above threshold: {results['latency']['p95_ms']}ms")
    
    # Check throughput
    if results["throughput_rps"] < 30:
        status = "fail"
        issues.append(f"Throughput too low: {results['throughput_rps']:.1f} rps")
    elif results["throughput_rps"] < 50:
        if status == "pass":
            status = "warning"
        issues.append(f"Throughput below target: {results['throughput_rps']:.1f} rps")
    
    return {
        "status": status,
        "issues": issues
    }
```

---

## 🔍 Phân tích kết quả

### 1. Identify Bottlenecks

- **High latency**: Có thể do:
  - LLM API slow
  - Database queries slow
  - Network latency
  - Processing time

- **Low throughput**: Có thể do:
  - Rate limiting
  - Server resources (CPU/RAM)
  - Database connection pool
  - Synchronous processing

- **High error rate**: Có thể do:
  - Timeouts
  - Rate limits exceeded
  - Resource exhaustion
  - Network issues

### 2. Compare Workload Levels

So sánh performance ở các mức tải khác nhau:

| Metric | Light (10) | Medium (50) | Heavy (100) | Extreme (500) |
|--------|------------|-------------|-------------|---------------|
| Throughput (rps) | 10 | 30 | 45 | 80 |
| Avg Latency (ms) | 2000 | 3000 | 4000 | 6000 |
| P95 Latency (ms) | 3000 | 4500 | 5500 | 8500 |
| Success Rate (%) | 99 | 97 | 95 | 90 |
| Error Rate (%) | 0.5 | 1.0 | 2.0 | 5.0 |

### 3. Recommendations

Dựa trên kết quả, đưa ra recommendations:

- **Nếu latency cao**: 
  - Optimize database queries
  - Add caching
  - Use faster models
  - Implement async processing

- **Nếu throughput thấp**:
  - Increase server resources
  - Implement connection pooling
  - Use load balancer
  - Optimize code

- **Nếu error rate cao**:
  - Increase timeout
  - Implement retry logic
  - Add circuit breaker
  - Scale horizontally

---

## 📝 Test Cases

### Test Case: CLASSS_S1_001 - 10 Concurrent Requests

```json
{
  "Test_Case_ID": "CLASSS_S1_001",
  "Feature_Area": "Scalability",
  "Description_VN": "Scalability - 10 concurrent requests",
  "User_Message_Input": "chi 50k test",
  "Precondition": "10 concurrent sessions",
  "Expected_Metrics": {
    "concurrent_requests": 10,
    "max_avg_latency_ms": 5000,
    "success_rate_min": 0.95,
    "throughput_rps_min": 10
  }
}
```

### Test Case: CLASSS_S1_002 - 50 Sequential Requests

```json
{
  "Test_Case_ID": "CLASSS_S1_002",
  "Feature_Area": "Scalability",
  "Description_VN": "Scalability - 50 sequential requests",
  "User_Message_Input": "chi {random}k test",
  "Precondition": "Single session, 50 requests",
  "Expected_Metrics": {
    "total_requests": 50,
    "success_rate_min": 0.98,
    "throughput_rps_min": 30
  }
}
```

---

## 🛠️ Tools và Scripts

### 1. Run Workload Test

```bash
# Test với 10 concurrent users
python test_workload.py --concurrent 10

# Test với 50 concurrent users
python test_workload.py --concurrent 50

# Test với ramp-up từ 10 đến 100
python test_workload.py --rampup --min 10 --max 100
```

### 2. Generate Report

```bash
# Generate workload report
python generate_workload_report.py --input workload_results.json --output workload_report.xlsx
```

---

## 📚 References

- `workload_thresholds.json`: File chứa tất cả thresholds
- `CLASS_METRICS_DOCUMENTATION.md`: Chi tiết về CLASS metrics
- `config.py`: Configuration và thresholds

---

*Last updated: 2025-12-25*
*Framework Version: 1.1.0*

