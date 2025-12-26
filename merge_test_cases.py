"""
Merge all test case files into one comprehensive test_cases_all.json
"""
import json
import sys
from datetime import datetime

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def merge_test_cases():
    """Merge all test case files into one comprehensive test suite"""
    
    # Files to merge (excluding test_cases_all.json itself)
    files = [
        ("test_cases.json", "Functional"),
        ("test_cases_security.json", "Security"),
        ("test_cases_classs.json", "C-L-A-S-S"),
        # REMOVED: test_cases_class_design.json - Not applicable for non-conversational chatbot
        # NEW: Test cases based on system prompts analysis
        ("test_cases_intent_edge.json", "Intent_Edge"),
        ("test_cases_amount_parsing.json", "Amount_Parsing"),
        ("test_cases_member_detection.json", "Member_Detection")
    ]
    
    all_test_cases = []
    
    for filename, category in files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tests = data.get("test_cases", [])
                
                # Add category tag to each test
                for test in tests:
                    test["Category"] = category
                
                all_test_cases.extend(tests)
                print(f"✅ Loaded {len(tests)} tests from {filename}")
        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")
    
    # Create merged file
    merged = {
        "metadata": {
            "project": "MoneyCare Chatbot AI",
            "version": "2.0.0",
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "framework": "C-L-A-S-S + OWASP LLM Top 10 + CLASS Design + System Prompts Validation",
            "description": "Comprehensive test suite including system prompts validation (intent edge cases, amount parsing, member detection)",
            "total_tests": len(all_test_cases),
            "categories": {
                "Functional": "TC_* - Basic chatbot functionality",
                "Security": "SEC_* - OWASP LLM Top 10 (LLM01, LLM02, LLM04, LLM06, LLM08, LLM09) - LLM05 N/A",
                "C-L-A-S-S": "CLASSS_* - Cost, Latency, Accuracy, Scalability, Stability",
                "Intent_Edge": "INTENT_EDGE_* - Intent detection edge cases (financial_question vs transaction)",
                "Amount_Parsing": "AMOUNT_* - Amount parsing validation (k, tr, m, b, decimal formats)",
                "Member_Detection": "MEMBER_* - Member detection (Tùng, Trang, Hiền)"
            },
            "environment": {
                "chatbot_url": "http://127.0.0.1:3333",
                "ai_client_url": "http://127.0.0.1:3334",
                "default_provider": "openai",
                "default_model": "gpt-4o-mini"
            },
            "last_merged": datetime.now().isoformat()
        },
        "test_cases": all_test_cases
    }
    
    # Write merged file
    with open("test_cases_all.json", 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Created test_cases_all.json with {len(all_test_cases)} total tests")
    
    # Summary by category
    print("\n📊 Summary by category:")
    categories = {}
    for test in all_test_cases:
        cat = test.get("Category", "Unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in categories.items():
        print(f"   {cat}: {count} tests")

if __name__ == "__main__":
    merge_test_cases()
