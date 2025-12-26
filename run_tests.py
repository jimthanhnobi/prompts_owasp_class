#!/usr/bin/env python3
"""
Main entry point for running MoneyCare Chatbot tests
"""
import argparse
import sys
import codecs
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from rich.console import Console
from rich.panel import Panel

from config import TestConfig
from test_runner import TestRunner
from report_generator import ReportGenerator


console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="MoneyCare Chatbot Test Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests from a file
  python run_tests.py -f test_cases.json
  
  # Run only security tests
  python run_tests.py -f test_cases_security.json --feature Security
  
  # Run only critical priority tests
  python run_tests.py -f test_cases.json --priority Critical
  
  # Run with custom environment
  python run_tests.py -f test_cases.json --env Production --url http://prod.example.com:3333
  
  # Export to different formats
  python run_tests.py -f test_cases.json --export excel
  python run_tests.py -f test_cases.json --export csv
  python run_tests.py -f test_cases.json --export json
        """
    )
    
    parser.add_argument(
        "--test-file", "-f",
        required=True,
        help="Path to test cases JSON file"
    )
    parser.add_argument(
        "--feature",
        help="Filter by feature area (e.g., Security, Transaction_Parse, Intent_Detection)"
    )
    parser.add_argument(
        "--priority",
        choices=["Critical", "High", "Medium", "Low"],
        help="Filter by priority level"
    )
    parser.add_argument(
        "--export", "-e",
        choices=["json", "csv", "excel"],
        default="excel",
        help="Export format (default: excel)"
    )
    parser.add_argument(
        "--env",
        default="Staging",
        help="Test environment name (default: Staging)"
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:3333",
        help="Chatbot API base URL (default: http://127.0.0.1:3333)"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="LLM model name (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Request timeout in milliseconds (default: 30000)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Validate test file exists
    test_file = Path(args.test_file)
    if not test_file.exists():
        console.print(f"[red]Error: Test file not found: {test_file}[/red]")
        sys.exit(1)
    
    # Create config
    config = TestConfig(
        chatbot_base_url=args.url,
        environment=args.env,
        llm_model=args.model,
        default_timeout_ms=args.timeout
    )
    
    # Print banner
    console.print(Panel(
        f"""[bold blue]MoneyCare Chatbot Test Framework[/bold blue]
        
Test File: {args.test_file}
Environment: {args.env}
API URL: {args.url}
Model: {args.model}
Export Format: {args.export}
""",
        title="Test Configuration",
        border_style="blue"
    ))
    
    # Create runner
    runner = TestRunner(config)
    
    # Load test cases
    console.print(f"\nLoading test cases from: {args.test_file}")
    try:
        test_cases = runner.load_test_cases(str(test_file))
        console.print(f"[green]Loaded {len(test_cases)} test cases[/green]")
    except Exception as e:
        console.print(f"[red]Error loading test cases: {e}[/red]")
        sys.exit(1)
    
    # Apply filters
    if args.feature:
        console.print(f"Filtering by feature: {args.feature}")
    if args.priority:
        console.print(f"Filtering by priority: {args.priority}")
    
    # Run tests
    console.print("\nStarting test execution...\n")
    
    try:
        results = runner.run_tests(
            test_cases,
            filter_feature=args.feature,
            filter_priority=args.priority
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Test execution interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error during test execution: {e}[/red]")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    # Print summary
    console.print("\n" + "=" * 60)
    runner.print_summary()
    
    # Print failed tests
    runner.print_failed_tests()
    
    # Generate report
    console.print("\nGenerating report...")
    
    report_paths = []
    
    # Always generate JSON (already saved by TestRunner, but verify)
    json_path = runner.results_file
    if json_path and Path(json_path).exists():
        console.print(f"[green]JSON report saved to: {json_path}[/green]")
        report_paths.append(json_path)
    else:
        json_path = runner.export_results("json")
        console.print(f"[green]JSON report saved to: {json_path}[/green]")
        report_paths.append(json_path)
    
    # Generate Excel if requested (default)
    if args.export == "excel":
        try:
            report_gen = ReportGenerator(config)
            excel_path = report_gen.generate_excel_report(
                runner.results,
                runner.summary,
                test_cases=test_cases  # Pass test cases for category sheets
            )
            console.print(f"[green]Excel report saved to: {excel_path}[/green]")
            report_paths.append(excel_path)
        except Exception as e:
            console.print(f"[red]Error generating Excel report: {e}[/red]")
            if args.verbose:
                import traceback
                traceback.print_exc()
    elif args.export != "json":
        # Generate other formats (CSV, etc.)
        other_path = runner.export_results(args.export)
        console.print(f"[green]{args.export.upper()} report saved to: {other_path}[/green]")
        report_paths.append(str(other_path))
    
    report_path = ", ".join(str(p) for p in report_paths) if report_paths else "N/A"
    
    # Final summary
    console.print(Panel(
        f"""[bold]Test Execution Complete[/bold]

Total: {runner.summary.total_tests}
Passed: [green]{runner.summary.passed}[/green]
Failed: [red]{runner.summary.failed}[/red]
Partial: [yellow]{runner.summary.partial}[/yellow]
Pass Rate: {runner.summary.pass_rate():.1f}%

Reports:
{chr(10).join('  ' + str(p) for p in report_paths) if report_paths else '  N/A'}
""",
        title="📋 Summary",
        border_style="green" if runner.summary.failed == 0 else "red"
    ))
    
    # Exit with appropriate code
    sys.exit(0 if runner.summary.failed == 0 else 1)


if __name__ == "__main__":
    main()
