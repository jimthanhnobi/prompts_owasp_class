"""
Cleanup unused files in moneycare-test-framework
"""
import os
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def cleanup_unused_files():
    """Remove unused/redundant files"""
    
    print("=" * 60)
    print("CLEANUP UNUSED FILES")
    print("=" * 60)
    print()
    
    # Files to remove
    files_to_remove = {
        # Debug/Test scripts (one-time use)
        "debug_jwt.py": "JWT debug script - not needed",
        "quick_test.py": "Quick test script - redundant",
        "test_auth_direct.py": "Auth test script - one-time use",
        "test_cost_calculation.py": "Cost test script - one-time use",
        "generate_test_cases.py": "Test generator - already used",
        
        # Redundant batch files
        "run_all_comprehensive.bat": "Batch file - use Python script",
        "run_all_tests.bat": "Batch file - use Python script",
        "run_security_tests.bat": "Batch file - use Python script",
        "run_all_tests_comprehensive.py": "Redundant with run_tests.py",
        
        # Redundant documentation
        "SUMMARY.md": "Old summary - superseded by newer docs",
        "IMPROVEMENTS_SUMMARY.md": "Old improvements - covered in CLEANUP_COMPLETE_SUMMARY.md",
        "STEP_2_MERGE_SUMMARY.md": "Merge step - covered in CLEANUP_COMPLETE_SUMMARY.md",
        
        # Backup file
        "test_cases_class_design.json.backup": "Backup - already removed",
    }
    
    removed_count = 0
    
    for filename, reason in files_to_remove.items():
        filepath = Path(filename)
        if filepath.exists():
            filepath.unlink()
            print(f"✅ Removed: {filename}")
            print(f"   Reason: {reason}")
            removed_count += 1
        else:
            print(f"⚠️  Not found: {filename}")
    
    print()
    print("=" * 60)
    print(f"✅ Removed {removed_count} files")
    print("=" * 60)
    print()
    
    return removed_count

def consolidate_documentation():
    """Consolidate documentation files"""
    
    print("=" * 60)
    print("DOCUMENTATION CONSOLIDATION RECOMMENDATIONS")
    print("=" * 60)
    print()
    
    docs = {
        "README.md": "Main README - KEEP",
        "README_V2.md": "Updated README - Consider merging with README.md",
        "QUICK_START.md": "Quick start guide - KEEP",
        "FINAL_SUMMARY.md": "Final summary - KEEP (most comprehensive)",
        "COMPLETION_SUMMARY.md": "Completion summary - Consider removing (covered by FINAL_SUMMARY)",
        "NEW_TEST_CASES_SUMMARY.md": "New tests summary - KEEP (detailed)",
        "CLEANUP_COMPLETE_SUMMARY.md": "Cleanup summary - KEEP (latest)",
        "TEST_CASES_ISSUES_ANALYSIS.md": "Issues analysis - KEEP (detailed analysis)",
        "SYSTEM_ARCHITECTURE_ANALYSIS.md": "System architecture - KEEP (important)",
        "SYSTEM_INSIGHTS.md": "System insights - KEEP (detailed findings)",
        "REQUIREMENT_GAP_ANALYSIS.md": "Gap analysis - KEEP",
        "CLASS_METRICS_DOCUMENTATION.md": "CLASS metrics - KEEP",
        "OWASP_COVERAGE_DOCUMENTATION.md": "OWASP coverage - KEEP",
        "WORKLOAD_EVALUATION_GUIDE.md": "Workload guide - KEEP",
        "REPORT_STRUCTURE.md": "Report structure - KEEP",
    }
    
    print("Current Documentation Files:")
    print()
    for doc, status in docs.items():
        filepath = Path(doc)
        exists = "✅" if filepath.exists() else "❌"
        print(f"{exists} {doc}")
        print(f"   {status}")
    
    print()
    print("Recommendation: Keep most docs as they serve different purposes")
    print()

def main():
    """Main cleanup"""
    
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "CLEANUP UNUSED FILES SCRIPT" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Step 1: Remove unused files
    removed = cleanup_unused_files()
    
    # Step 2: Documentation recommendations
    consolidate_documentation()
    
    # Summary
    print("=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)
    print(f"✅ Removed {removed} unused files")
    print("✅ Documentation files reviewed")
    print()
    print("Next: Fix accuracy scoring in evaluator.py")
    print()

if __name__ == "__main__":
    main()


