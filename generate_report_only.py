"""
Generate report from existing test results JSON
Usage: python generate_report_only.py [json_file_path]
"""
import json
import sys
from datetime import datetime
from pathlib import Path

from config import TestConfig
from models import TestRunResult, TestSummary, PassFailStatus, SecurityObservation, StabilityObservation
from report_generator import ReportGenerator


def load_results_from_json(json_path: str):
    """Load test results from JSON file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = []
    for r in data.get("results", []):
        result = TestRunResult(
            test_run_id=r.get("Test_Run_ID", ""),
            test_case_id=r.get("Test_Case_ID", ""),
            date=r.get("Date", ""),
            tester=r.get("Tester", ""),
            environment=r.get("Environment", ""),
            llm_model=r.get("LLM_Model", ""),
            actual_bot_response=r.get("Actual_Bot_Response", ""),
            actual_parsed_transaction=r.get("Actual_Parsed_Transaction"),
            pass_fail=PassFailStatus(r.get("Pass_Fail", "Fail")),
            issues_found=r.get("Issues_Found", False),
            issue_ids=r.get("Issue_IDs", []),
            measured_latency_ms=r.get("Measured_Latency_ms", 0),
            measured_cost_vnd=r.get("Measured_Cost_VND", 0),
            accuracy_score_percent=r.get("Accuracy_Score_percent", 0),
            security_observation=SecurityObservation(r.get("Security_Observation", "OK")),
            stability_observation=StabilityObservation(r.get("Stability_Observation", "OK")),
            notes=r.get("Notes", "")
        )
        results.append(result)
    
    # Get test cases from the same file if available
    test_cases = data.get("test_cases", [])
    
    # Get run info
    run_info = data.get("run_info", {})
    
    return results, test_cases, run_info


def calculate_summary(results):
    """Calculate summary from results"""
    summary = TestSummary()
    summary.total_tests = len(results)
    summary.passed = len([r for r in results if r.pass_fail == PassFailStatus.PASS])
    summary.failed = len([r for r in results if r.pass_fail == PassFailStatus.FAIL])
    summary.partial = len([r for r in results if r.pass_fail == PassFailStatus.PARTIAL])
    summary.errors = len([r for r in results if r.pass_fail == PassFailStatus.ERROR])
    summary.skipped = len([r for r in results if r.pass_fail == PassFailStatus.SKIP])
    summary.avg_latency_ms = sum(r.measured_latency_ms for r in results) / len(results) if results else 0
    # Only count tests that have accuracy scores (tests with expected_parsed_transaction)
    accuracy_scores = [r.accuracy_score_percent for r in results if r.accuracy_score_percent > 0]
    summary.avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
    summary.security_issues = len([r for r in results if r.security_observation != SecurityObservation.OK])
    summary.stability_issues = len([r for r in results if r.stability_observation != StabilityObservation.OK])
    summary.start_time = datetime.now()
    summary.end_time = datetime.now()
    return summary


def find_latest_json():
    """Find the most recent JSON results file"""
    results_dir = Path("test_results")
    if not results_dir.exists():
        return None
    
    json_files = list(results_dir.glob("test_run_*.json"))
    if not json_files:
        # Try old format
        json_files = list(results_dir.glob("test_results_*.json"))
    
    if not json_files:
        return None
    
    return max(json_files, key=lambda p: p.stat().st_mtime)


def main():
    # Get JSON file path from argument or find latest
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        json_path = find_latest_json()
        if not json_path:
            print("❌ No JSON result files found in test_results/")
            print("   Run tests first: python run_tests.py -f test_cases_all.json")
            return
    
    print(f"📂 Loading results from: {json_path}")
    
    # Load results
    results, test_cases, run_info = load_results_from_json(str(json_path))
    
    if not results:
        print("❌ No test results found in the JSON file")
        return
    
    print(f"   Found {len(results)} test results")
    
    # If no test cases in JSON, load from test_cases_all.json
    if not test_cases:
        test_cases_file = Path("test_cases_all.json")
        if test_cases_file.exists():
            with open(test_cases_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            test_cases = test_data.get("test_cases", [])
            print(f"   Loaded {len(test_cases)} test case definitions")
    
    # Calculate summary
    summary = calculate_summary(results)
    
    # Generate report
    config = TestConfig()
    report_gen = ReportGenerator(config)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"test_results/full_report_{timestamp}.xlsx"
    
    report_path = report_gen.generate_excel_report(
        results, 
        summary, 
        test_cases=test_cases, 
        output_path=output_path
    )
    
    print(f"\n✅ Report generated: {report_path}")
    print(f"\n📊 Summary:")
    print(f"   Total Tests: {summary.total_tests}")
    print(f"   Passed: {summary.passed} ({summary.pass_rate():.1f}%)")
    print(f"   Failed: {summary.failed}")
    print(f"   Partial: {summary.partial}")
    print(f"   Errors: {summary.errors}")
    print(f"   Security Issues: {summary.security_issues}")
    print(f"   Stability Issues: {summary.stability_issues}")
    print(f"   Avg Latency: {summary.avg_latency_ms:.0f} ms")


if __name__ == "__main__":
    main()
