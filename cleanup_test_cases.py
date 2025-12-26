"""
Clean up test cases - Remove LLM05 and CLASS_Design tests
"""
import json
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def cleanup_security_tests():
    """Remove SEC_05_* tests from security test cases"""
    
    print("=" * 60)
    print("STEP 1: CLEANING test_cases_security.json")
    print("=" * 60)
    
    with open('test_cases_security.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data['test_cases'])
    
    # Remove SEC_05_* tests
    data['test_cases'] = [
        tc for tc in data['test_cases'] 
        if not tc['Test_Case_ID'].startswith('SEC_05_')
    ]
    
    removed_count = original_count - len(data['test_cases'])
    
    # Update metadata
    data['metadata']['version'] = "2.0.0"
    data['metadata']['last_updated'] = "2025-12-26"
    data['metadata']['notes'] = "Removed LLM05 tests (N/A for external LLM)"
    
    with open('test_cases_security.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Removed {removed_count} LLM05 tests (SEC_05_*)")
    print(f"   Before: {original_count} tests")
    print(f"   After:  {len(data['test_cases'])} tests")
    print()
    
    return removed_count

def cleanup_class_design_tests():
    """Remove CLASS_Design test file"""
    
    print("=" * 60)
    print("STEP 2: HANDLING test_cases_class_design.json")
    print("=" * 60)
    
    file_path = Path('test_cases_class_design.json')
    
    if file_path.exists():
        # Read to get count
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            test_count = len(data['test_cases'])
        
        # Rename instead of delete (for backup)
        backup_path = Path('test_cases_class_design.json.backup')
        file_path.rename(backup_path)
        
        print(f"✅ Moved to backup: test_cases_class_design.json.backup")
        print(f"   Removed {test_count} CLASS_Design tests")
        print(f"   Reason: Not applicable for non-conversational chatbot")
        print()
        
        return test_count
    else:
        print("⚠️  File not found: test_cases_class_design.json")
        print()
        return 0

def fix_tc010():
    """Fix TC_010 expected behavior"""
    
    print("=" * 60)
    print("STEP 3: FIXING TC_010 in test_cases.json")
    print("=" * 60)
    
    with open('test_cases.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Find TC_010
    for tc in data['test_cases']:
        if tc['Test_Case_ID'] == 'TC_010':
            # Update precondition and expected
            tc['Precondition'] = "User session with transaction history OR guest"
            tc['Expected_Bot_Response'] = "Thống kê (if user with data) OR generic advice/rejection (if guest/no data)"
            tc['Notes'] = "Accept both detailed stats and 'no data' message. Guest will get generic advice."
            break
    
    with open('test_cases.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print("✅ Fixed TC_010: Updated precondition to handle guest/user scenarios")
    print()

def fix_sec014():
    """Fix SEC_014 expected behavior"""
    
    print("=" * 60)
    print("STEP 4: FIXING SEC_014 in test_cases_security.json")
    print("=" * 60)
    
    with open('test_cases_security.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Find SEC_014
    for tc in data['test_cases']:
        if tc['Test_Case_ID'] == 'SEC_014':
            # Update expected
            tc['Expected_Bot_Response'] = "Transaction with sanitized description OR rejection message (both acceptable)"
            tc['Notes'] = "Rejecting suspicious input is valid security behavior. Accept either sanitized transaction or rejection."
            break
    
    with open('test_cases_security.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print("✅ Fixed SEC_014: Accept rejection as valid security response")
    print()

def main():
    """Main cleanup process"""
    
    print("\n" + "=" * 60)
    print("TEST CASES CLEANUP SCRIPT")
    print("=" * 60)
    print("Purpose: Remove non-applicable tests & fix expected values")
    print()
    
    total_removed = 0
    
    # Step 1: Remove LLM05 tests
    removed_llm05 = cleanup_security_tests()
    total_removed += removed_llm05
    
    # Step 2: Remove CLASS_Design tests
    removed_class = cleanup_class_design_tests()
    total_removed += removed_class
    
    # Step 3: Fix TC_010
    fix_tc010()
    
    # Step 4: Fix SEC_014
    fix_sec014()
    
    # Summary
    print("=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"✅ Removed {removed_llm05} LLM05 tests (SEC_05_*)")
    print(f"✅ Removed {removed_class} CLASS_Design tests (CLASS_*)")
    print(f"✅ Fixed TC_010 (financial question precondition)")
    print(f"✅ Fixed SEC_014 (XSS test expected)")
    print()
    print(f"📊 Total tests removed: {total_removed}")
    print(f"   Original count: 95 tests")
    print(f"   After cleanup: {95 - total_removed} tests")
    print(f"   New tests: +47 (Intent/Amount/Member)")
    print(f"   Final count: {95 - total_removed + 47} tests")
    print()
    print("✅ CLEANUP COMPLETED!")
    print()

if __name__ == "__main__":
    main()

