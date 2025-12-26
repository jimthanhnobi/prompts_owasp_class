"""
Test Runner - Executes test cases and collects results
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel

from config import TestConfig
from models import TestCase, TestRunResult, TestSummary, PassFailStatus
from api_client import MoneyCareAPIClient, TestIdentity
from evaluator import TestEvaluator


console = Console()


class TestRunner:
    """Runs test cases and collects results"""
    
    def __init__(self, config: Optional[TestConfig] = None, identity: Optional[TestIdentity] = None):
        self.config = config or TestConfig()
        self.identity = identity or TestIdentity.from_config_file()
        self.api_client = MoneyCareAPIClient(self.config, self.identity)
        self.evaluator = TestEvaluator(self.config)
        self.results: List[TestRunResult] = []
        self.summary = TestSummary()
        
        # Single consolidated results file
        self.results_file: Optional[Path] = None
        self.test_cases_data: List[Dict] = []  # Store original test case data
        
        # Ensure directories exist
        Path(self.config.results_dir).mkdir(parents=True, exist_ok=True)
    
    def load_test_cases(self, file_path: str) -> List[TestCase]:
        """Load test cases from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        test_cases = []
        self.test_cases_data = data.get("test_cases", [])  # Store raw data
        for tc_data in self.test_cases_data:
            test_cases.append(TestCase.from_dict(tc_data))
        
        return test_cases
    
    def _init_results_file(self):
        """Initialize the consolidated results file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_file = Path(self.config.results_dir) / f"test_run_{timestamp}.json"
        
        # Create initial structure
        initial_data = {
            "run_info": {
                "start_time": datetime.now().isoformat(),
                "environment": self.config.environment,
                "llm_model": self.config.llm_model,
                "status": "running"
            },
            "summary": self.summary.to_dict(),
            "results": [],
            "test_cases": self.test_cases_data
        }
        
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)
        
        console.print(f"[cyan]Results will be saved to: {self.results_file}[/cyan]")
    
    def _save_incremental(self, result: TestRunResult):
        """Save result incrementally to the consolidated JSON file"""
        if not self.results_file:
            return
        
        # Read current data
        with open(self.results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add new result
        data["results"].append(result.to_dict())
        data["summary"] = self.summary.to_dict()
        data["run_info"]["last_updated"] = datetime.now().isoformat()
        
        # Write back
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _finalize_results_file(self):
        """Mark the results file as complete"""
        if not self.results_file:
            return
        
        with open(self.results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data["run_info"]["end_time"] = datetime.now().isoformat()
        data["run_info"]["status"] = "completed"
        data["summary"] = self.summary.to_dict()
        
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _export_failed_tests(self):
        """Export failed tests to separate file for analysis"""
        # Get failed tests
        failed_results = [
            r for r in self.results 
            if r.pass_fail in [PassFailStatus.FAIL, PassFailStatus.ERROR, PassFailStatus.PARTIAL]
        ]
        
        if not failed_results:
            # No failed tests, skip
            return
        
        # Get failed test case IDs
        failed_test_ids = {r.test_case_id for r in failed_results}
        failed_test_cases = [
            tc for tc in self.test_cases_data 
            if tc.get("Test_Case_ID") in failed_test_ids
        ]
        
        # Prepare failed tests data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        failed_file = Path(self.config.results_dir) / f"failed_tests_{timestamp}.json"
        
        failed_data = {
            "run_info": {
                "timestamp": datetime.now().isoformat(),
                "environment": self.config.environment,
                "llm_model": self.config.llm_model,
                "total_tests": self.summary.total_tests,
                "failed_count": len(failed_results),
                "fail_rate": (len(failed_results) / self.summary.total_tests * 100) if self.summary.total_tests > 0 else 0
            },
            "summary": {
                "total_failed": len(failed_results),
                "by_status": {},
                "by_feature": {},
                "by_priority": {}
            },
            "failed_results": [r.to_dict() for r in failed_results],
            "failed_test_cases": failed_test_cases
        }
        
        # Analyze failures
        test_case_map = {tc.get("Test_Case_ID"): tc for tc in failed_test_cases}
        
        for result in failed_results:
            # By status
            status = result.pass_fail.value
            failed_data["summary"]["by_status"][status] = failed_data["summary"]["by_status"].get(status, 0) + 1
            
            # By feature and priority
            test_case = test_case_map.get(result.test_case_id, {})
            feature = test_case.get("Feature_Area", "Unknown")
            priority = test_case.get("Priority", "Unknown")
            
            failed_data["summary"]["by_feature"][feature] = failed_data["summary"]["by_feature"].get(feature, 0) + 1
            failed_data["summary"]["by_priority"][priority] = failed_data["summary"]["by_priority"].get(priority, 0) + 1
        
        # Save to file
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed_data, f, ensure_ascii=False, indent=2)
        
        console.print(f"[yellow]Failed tests exported to: {failed_file}[/yellow]")
    
    def run_single_test(self, test_case: TestCase) -> TestRunResult:
        """Run a single test case"""
        # Initialize session
        init_response = self.api_client.init_session()
        if not init_response.success:
            return self.evaluator.evaluate(
                test_case=test_case,
                actual_response="",
                actual_parsed=None,
                latency_ms=init_response.latency_ms,
                error=f"Session init failed: {init_response.error}"
            )
        
        # Send test message
        ask_response = self.api_client.ask(test_case.user_message_input)
        
        if not ask_response.success:
            result = self.evaluator.evaluate(
                test_case=test_case,
                actual_response="",
                actual_parsed=None,
                latency_ms=ask_response.latency_ms,
                error=ask_response.error
            )
        else:
            # Parse response
            answer, parsed_transaction = self.api_client.parse_bot_response(
                ask_response.data or {}
            )
            
            # Estimate token usage and calculate cost
            token_usage = self.api_client.estimate_token_usage(
                question=test_case.user_message_input,
                answer=answer
            )
            cost_vnd = self.evaluator.calculate_cost(
                prompt_tokens=token_usage["prompt_tokens"],
                completion_tokens=token_usage["completion_tokens"]
            )
            
            # Evaluate
            result = self.evaluator.evaluate(
                test_case=test_case,
                actual_response=answer,
                actual_parsed=parsed_transaction,
                latency_ms=ask_response.latency_ms
            )
            
            # Set token usage and cost
            result.token_usage = token_usage
            result.measured_cost_vnd = cost_vnd
        
        # Store raw data
        result.raw_request = {
            "question": test_case.user_message_input,
            "fingerprint": self.api_client.fingerprint
        }
        result.raw_response = ask_response.data
        
        # Reset session for next test
        self.api_client.reset_session()
        
        return result
    
    def run_tests(
        self,
        test_cases: List[TestCase],
        filter_feature: Optional[str] = None,
        filter_priority: Optional[str] = None
    ) -> List[TestRunResult]:
        """Run multiple test cases"""
        self.results = []
        self.summary = TestSummary()
        self.summary.start_time = datetime.now()
        
        # Filter test cases
        filtered_cases = test_cases
        if filter_feature:
            filtered_cases = [tc for tc in filtered_cases if tc.feature_area == filter_feature]
        if filter_priority:
            filtered_cases = [tc for tc in filtered_cases if tc.priority == filter_priority]
        
        self.summary.total_tests = len(filtered_cases)
        
        # Initialize consolidated results file
        self._init_results_file()
        
        console.print(Panel(
            f"[bold blue]Running {len(filtered_cases)} test cases[/bold blue]\n"
            f"Environment: {self.config.environment}\n"
            f"Model: {self.config.llm_model}\n"
            f"Results: {self.results_file}",
            title="MoneyCare Test Framework"
        ))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Running tests...", total=len(filtered_cases))
            
            for test_case in filtered_cases:
                progress.update(task, description=f"Running {test_case.test_case_id}...")
                
                result = self.run_single_test(test_case)
                self.results.append(result)
                
                # Update summary
                self._update_summary(result)
                
                # Save incrementally to single JSON file
                self._save_incremental(result)
                
                progress.advance(task)
        
        self.summary.end_time = datetime.now()
        
        # Calculate averages
        if self.results:
            self.summary.avg_latency_ms = sum(r.measured_latency_ms for r in self.results) / len(self.results)
            accuracy_scores = [r.accuracy_score_percent for r in self.results if r.accuracy_score_percent > 0]
            if accuracy_scores:
                self.summary.avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)
        
        # Finalize results file
        self._finalize_results_file()
        
        # Export failed tests if any
        self._export_failed_tests()
        
        return self.results
    
    def _update_summary(self, result: TestRunResult):
        """Update summary with result"""
        if result.pass_fail == PassFailStatus.PASS:
            self.summary.passed += 1
        elif result.pass_fail == PassFailStatus.FAIL:
            self.summary.failed += 1
        elif result.pass_fail == PassFailStatus.PARTIAL:
            self.summary.partial += 1
        elif result.pass_fail == PassFailStatus.ERROR:
            self.summary.errors += 1
        else:
            self.summary.skipped += 1
        
        self.summary.total_cost_vnd += result.measured_cost_vnd
        
        if result.security_observation.value != "OK":
            self.summary.security_issues += 1
        if result.stability_observation.value != "OK":
            self.summary.stability_issues += 1
    
    def print_summary(self):
        """Print test summary to console"""
        table = Table(title="Test Results Summary")
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Total Tests", str(self.summary.total_tests))
        table.add_row("Passed", f"[green]{self.summary.passed}[/green]")
        table.add_row("Failed", f"[red]{self.summary.failed}[/red]")
        table.add_row("Partial", f"[yellow]{self.summary.partial}[/yellow]")
        table.add_row("Errors", f"[red]{self.summary.errors}[/red]")
        table.add_row("Pass Rate", f"{self.summary.pass_rate():.1f}%")
        table.add_row("Avg Latency", f"{self.summary.avg_latency_ms:.0f} ms")
        table.add_row("Avg Accuracy", f"{self.summary.avg_accuracy:.1f}%")
        table.add_row("Security Issues", f"[red]{self.summary.security_issues}[/red]")
        table.add_row("Stability Issues", f"[yellow]{self.summary.stability_issues}[/yellow]")
        
        console.print(table)
    
    def print_failed_tests(self):
        """Print details of failed tests"""
        failed = [r for r in self.results if r.pass_fail in [PassFailStatus.FAIL, PassFailStatus.ERROR]]
        
        if not failed:
            console.print("[green]No failed tests![/green]")
            return
        
        console.print(f"\n[red]Failed Tests ({len(failed)}):[/red]")
        
        for result in failed:
            console.print(Panel(
                f"[bold]{result.test_case_id}[/bold]\n"
                f"Status: {result.pass_fail.value}\n"
                f"Security: {result.security_observation.value}\n"
                f"Stability: {result.stability_observation.value}\n"
                f"Accuracy: {result.accuracy_score_percent:.1f}%\n"
                f"Notes: {result.notes}",
                title=result.test_case_id,
                border_style="red"
            ))
    
    def export_results(self, format: str = "json") -> str:
        """Export results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            # Results already saved incrementally, just return the path
            if self.results_file and self.results_file.exists():
                console.print(f"[green]Results already saved to: {self.results_file}[/green]")
                return str(self.results_file)
            
            # Fallback: create new file
            file_path = Path(self.config.results_dir) / f"test_results_{timestamp}.json"
            data = {
                "run_info": {
                    "start_time": self.summary.start_time.isoformat() if self.summary.start_time else None,
                    "end_time": self.summary.end_time.isoformat() if self.summary.end_time else None,
                    "environment": self.config.environment,
                    "llm_model": self.config.llm_model,
                    "status": "completed"
                },
                "summary": self.summary.to_dict(),
                "results": [r.to_dict() for r in self.results],
                "test_cases": self.test_cases_data
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            console.print(f"[green]Results exported to: {file_path}[/green]")
            return str(file_path)
        
        elif format == "csv":
            import pandas as pd
            file_path = Path(self.config.results_dir) / f"test_results_{timestamp}.csv"
            df = pd.DataFrame([r.to_dict() for r in self.results])
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        elif format == "excel":
            import pandas as pd
            file_path = Path(self.config.results_dir) / f"test_results_{timestamp}.xlsx"
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Summary sheet
                summary_df = pd.DataFrame([self.summary.to_dict()])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Results sheet
                results_df = pd.DataFrame([r.to_dict() for r in self.results])
                results_df.to_excel(writer, sheet_name='Test Results', index=False)
                
                # Failed tests sheet
                failed = [r for r in self.results if r.pass_fail in [PassFailStatus.FAIL, PassFailStatus.ERROR]]
                if failed:
                    failed_df = pd.DataFrame([r.to_dict() for r in failed])
                    failed_df.to_excel(writer, sheet_name='Failed Tests', index=False)
                
                # Security issues sheet
                security_issues = [r for r in self.results if r.security_observation.value != "OK"]
                if security_issues:
                    security_df = pd.DataFrame([r.to_dict() for r in security_issues])
                    security_df.to_excel(writer, sheet_name='Security Issues', index=False)
        
        console.print(f"[green]Results exported to: {file_path}[/green]")
        return str(file_path)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MoneyCare Chatbot Test Framework")
    parser.add_argument("--test-file", "-f", required=True, help="Path to test cases JSON file")
    parser.add_argument("--feature", help="Filter by feature area")
    parser.add_argument("--priority", help="Filter by priority (Critical, High, Medium, Low)")
    parser.add_argument("--export", "-e", choices=["json", "csv", "excel"], default="excel",
                       help="Export format")
    parser.add_argument("--env", default="Staging", help="Test environment")
    
    args = parser.parse_args()
    
    # Create config
    config = TestConfig(environment=args.env)
    
    # Create runner
    runner = TestRunner(config)
    
    # Load test cases
    console.print(f"Loading test cases from: {args.test_file}")
    test_cases = runner.load_test_cases(args.test_file)
    console.print(f"Loaded {len(test_cases)} test cases")
    
    # Run tests
    runner.run_tests(
        test_cases,
        filter_feature=args.feature,
        filter_priority=args.priority
    )
    
    # Print results
    runner.print_summary()
    runner.print_failed_tests()
    
    # Export
    runner.export_results(args.export)


if __name__ == "__main__":
    main()
