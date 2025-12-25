"""
Merge all test case files into one comprehensive test_cases_all.json
"""
import json
from datetime import datetime

def merge_test_cases():
    """Merge all test case files into one"""
    
    # Files to merge
    files = [
        ("test_cases.json", "Functional"),
        ("test_cases_security.json", "Security"),
        ("test_cases_classs.json", "C-L-A-S-S"),
        ("test_cases_class_design.json", "CLASS_Design")
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
            "version": "1.0.0",
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "framework": "C-L-A-S-S + OWASP LLM Top 10 + CLASS Design",
            "description": "Comprehensive test suite combining all test categories",
            "total_tests": len(all_test_cases),
            "categories": {
                "Functional": "TC_* - Basic chatbot functionality",
                "Security": "SEC_* - OWASP LLM Top 10",
                "C-L-A-S-S": "CLASSS_* - Cost, Latency, Accuracy, Scalability, Stability",
                "CLASS_Design": "CLASS_* - UX/Interaction design principles"
            },
            "environment": {
                "chatbot_url": "http://127.0.0.1:3333",
                "ai_client_url": "http://127.0.0.1:3334",
                "default_provider": "openai",
                "default_model": "gpt-4o-mini"
            }
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
