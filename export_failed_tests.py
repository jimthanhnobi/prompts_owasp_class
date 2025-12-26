#!/usr/bin/env python3
"""
Export Failed Tests - Extract failed tests from JSON results for analysis

Usage:
    python export_failed_tests.py test_results/test_run_20251226_022350.json
    
Output:
    - failed_tests_YYYYMMDD_HHMMSS.json: Failed tests only
    - failed_tests_analysis_YYYYMMDD_HHMMSS.txt: Human-readable analysis
"""
import json
import sys
import codecs
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def extract_failed_tests(json_path: str) -> tuple:
    """
    Extract failed tests from JSON results
    
    Returns: (failed_results, failed_test_cases, summary_info)
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_results = data.get("results", [])
    all_test_cases = data.get("test_cases", [])
    run_info = data.get("run_info", {})
    summary = data.get("summary", {})
    
    # Filter failed tests
    failed_results = [
        r for r in all_results 
        if r.get("Pass_Fail") in ["Fail", "Error", "Partial"]
    ]
    
    # Get corresponding test cases
    failed_test_ids = {r.get("Test_Case_ID") for r in failed_results}
    failed_test_cases = [
        tc for tc in all_test_cases 
        if tc.get("Test_Case_ID") in failed_test_ids
    ]
    
    summary_info = {
        "total_tests": summary.get("Total_Tests", len(all_results)),
        "failed_count": len(failed_results),
        "passed_count": summary.get("Passed", 0),
        "fail_rate": (len(failed_results) / len(all_results) * 100) if all_results else 0,
        "run_info": run_info,
        "timestamp": datetime.now().isoformat()
    }
    
    return failed_results, failed_test_cases, summary_info


def analyze_failed_tests(failed_results: List[Dict], failed_test_cases: List[Dict]) -> Dict[str, Any]:
    """Analyze failed tests to find patterns"""
    
    analysis = {
        "total_failed": len(failed_results),
        "by_status": {},
        "by_feature": {},
        "by_priority": {},
        "by_security_observation": {},
        "by_stability_observation": {},
        "common_issues": [],
        "high_severity_failures": []
    }
    
    # Group by status
    for result in failed_results:
        status = result.get("Pass_Fail", "Unknown")
        analysis["by_status"][status] = analysis["by_status"].get(status, 0) + 1
    
    # Group by feature and priority
    test_case_map = {tc.get("Test_Case_ID"): tc for tc in failed_test_cases}
    
    for result in failed_results:
        test_id = result.get("Test_Case_ID")
        test_case = test_case_map.get(test_id, {})
        
        # By feature
        feature = test_case.get("Feature_Area", "Unknown")
        analysis["by_feature"][feature] = analysis["by_feature"].get(feature, 0) + 1
        
        # By priority
        priority = test_case.get("Priority", "Unknown")
        analysis["by_priority"][priority] = analysis["by_priority"].get(priority, 0) + 1
        
        # Security/Stability observations
        sec_obs = result.get("Security_Observation", "OK")
        stab_obs = result.get("Stability_Observation", "OK")
        
        if sec_obs != "OK":
            analysis["by_security_observation"][sec_obs] = analysis["by_security_observation"].get(sec_obs, 0) + 1
        
        if stab_obs != "OK":
            analysis["by_stability_observation"][stab_obs] = analysis["by_stability_observation"].get(stab_obs, 0) + 1
        
        # High severity failures
        severity = test_case.get("Severity_if_Failed", "")
        if severity in ["Critical", "High"]:
            analysis["high_severity_failures"].append({
                "test_id": test_id,
                "feature": feature,
                "severity": severity,
                "description": test_case.get("Description_VN", ""),
                "error": result.get("Notes", "")
            })
    
    return analysis


def generate_analysis_report(
    failed_results: List[Dict], 
    failed_test_cases: List[Dict], 
    summary_info: Dict,
    analysis: Dict
) -> str:
    """Generate human-readable analysis report"""
    
    report = []
    report.append("=" * 80)
    report.append("FAILED TESTS ANALYSIS REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {summary_info['timestamp']}")
    report.append(f"Total Tests: {summary_info['total_tests']}")
    report.append(f"Failed: {summary_info['failed_count']} ({summary_info['fail_rate']:.1f}%)")
    report.append(f"Passed: {summary_info['passed_count']}")
    report.append("")
    
    # Summary by status
    report.append("-" * 80)
    report.append("FAILURE BREAKDOWN BY STATUS")
    report.append("-" * 80)
    for status, count in sorted(analysis["by_status"].items(), key=lambda x: -x[1]):
        report.append(f"  {status:15s}: {count:3d} tests")
    report.append("")
    
    # By feature area
    report.append("-" * 80)
    report.append("FAILURES BY FEATURE AREA")
    report.append("-" * 80)
    for feature, count in sorted(analysis["by_feature"].items(), key=lambda x: -x[1]):
        report.append(f"  {feature:30s}: {count:3d} tests")
    report.append("")
    
    # By priority
    report.append("-" * 80)
    report.append("FAILURES BY PRIORITY")
    report.append("-" * 80)
    for priority, count in sorted(analysis["by_priority"].items(), key=lambda x: -x[1]):
        report.append(f"  {priority:15s}: {count:3d} tests")
    report.append("")
    
    # Security/Stability issues
    if analysis["by_security_observation"]:
        report.append("-" * 80)
        report.append("SECURITY OBSERVATIONS")
        report.append("-" * 80)
        for obs, count in analysis["by_security_observation"].items():
            report.append(f"  {obs:30s}: {count:3d} tests")
        report.append("")
    
    if analysis["by_stability_observation"]:
        report.append("-" * 80)
        report.append("STABILITY OBSERVATIONS")
        report.append("-" * 80)
        for obs, count in analysis["by_stability_observation"].items():
            report.append(f"  {obs:30s}: {count:3d} tests")
        report.append("")
    
    # High severity failures
    if analysis["high_severity_failures"]:
        report.append("-" * 80)
        report.append("HIGH SEVERITY FAILURES (CRITICAL/HIGH)")
        report.append("-" * 80)
        for failure in analysis["high_severity_failures"]:
            report.append(f"\n[{failure['test_id']}] {failure['severity']} - {failure['feature']}")
            report.append(f"  Description: {failure['description']}")
            report.append(f"  Error: {failure['error'][:200]}...")
        report.append("")
    
    # Detailed failed tests
    report.append("-" * 80)
    report.append("DETAILED FAILED TESTS")
    report.append("-" * 80)
    
    test_case_map = {tc.get("Test_Case_ID"): tc for tc in failed_test_cases}
    
    for i, result in enumerate(failed_results, 1):
        test_id = result.get("Test_Case_ID")
        test_case = test_case_map.get(test_id, {})
        
        report.append(f"\n{i}. [{test_id}] {result.get('Pass_Fail', 'Unknown')}")
        report.append(f"   Feature: {test_case.get('Feature_Area', 'Unknown')}")
        report.append(f"   Priority: {test_case.get('Priority', 'Unknown')}")
        report.append(f"   Description: {test_case.get('Description_VN', 'N/A')}")
        report.append(f"   Input: {test_case.get('User_Message_Input', 'N/A')[:100]}")
        report.append(f"   Expected: {test_case.get('Expected_Bot_Response', 'N/A')[:100]}")
        report.append(f"   Actual: {result.get('Actual_Bot_Response', 'N/A')[:150]}...")
        report.append(f"   Latency: {result.get('Measured_Latency_ms', 0)}ms")
        report.append(f"   Cost: {result.get('Measured_Cost_VND', 0):.2f} VND")
        report.append(f"   Accuracy: {result.get('Accuracy_Score_percent', 0):.1f}%")
        report.append(f"   Security: {result.get('Security_Observation', 'Unknown')}")
        report.append(f"   Stability: {result.get('Stability_Observation', 'Unknown')}")
        report.append(f"   Notes: {result.get('Notes', 'No notes')[:200]}")
    
    report.append("")
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python export_failed_tests.py <json_file_path>")
        print("\nExample:")
        print("  python export_failed_tests.py test_results/test_run_20251226_022350.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    if not Path(json_path).exists():
        print(f"❌ Error: File not found: {json_path}")
        sys.exit(1)
    
    print(f"📂 Loading test results from: {json_path}")
    
    # Extract failed tests
    failed_results, failed_test_cases, summary_info = extract_failed_tests(json_path)
    
    print(f"   Total tests: {summary_info['total_tests']}")
    print(f"   Failed tests: {summary_info['failed_count']} ({summary_info['fail_rate']:.1f}%)")
    
    if not failed_results:
        print("\n✅ No failed tests found! All tests passed!")
        return
    
    # Analyze
    analysis = analyze_failed_tests(failed_results, failed_test_cases)
    
    # Prepare output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("test_results")
    output_dir.mkdir(exist_ok=True)
    
    # 1. Export failed tests JSON
    failed_json_path = output_dir / f"failed_tests_{timestamp}.json"
    failed_data = {
        "summary": summary_info,
        "analysis": analysis,
        "failed_results": failed_results,
        "failed_test_cases": failed_test_cases
    }
    
    with open(failed_json_path, 'w', encoding='utf-8') as f:
        json.dump(failed_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Failed tests JSON saved to: {failed_json_path}")
    
    # 2. Generate analysis report
    report_txt = generate_analysis_report(failed_results, failed_test_cases, summary_info, analysis)
    report_path = output_dir / f"failed_tests_analysis_{timestamp}.txt"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_txt)
    
    print(f"✅ Analysis report saved to: {report_path}")
    
    # 3. Print summary to console
    print("\n" + "=" * 80)
    print("QUICK SUMMARY")
    print("=" * 80)
    print(f"Total Failed: {analysis['total_failed']}")
    print(f"\nBy Status:")
    for status, count in sorted(analysis["by_status"].items()):
        print(f"  {status}: {count}")
    print(f"\nBy Feature:")
    for feature, count in sorted(analysis["by_feature"].items(), key=lambda x: -x[1])[:5]:
        print(f"  {feature}: {count}")
    
    if analysis["high_severity_failures"]:
        print(f"\n⚠️  High Severity Failures: {len(analysis['high_severity_failures'])}")
        for failure in analysis["high_severity_failures"][:3]:
            print(f"  - {failure['test_id']}: {failure['description'][:60]}")
    
    print("\n" + "=" * 80)
    print(f"📊 Full analysis available in: {report_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()

