"""
Data models for test framework
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import json


class PassFailStatus(Enum):
    PASS = "Pass"
    FAIL = "Fail"
    PARTIAL = "Partial"
    SKIP = "Skip"
    ERROR = "Error"


class SecurityObservation(Enum):
    OK = "OK"
    PROMPT_INJECTION_ATTEMPT = "Prompt_injection_attempt_detected"
    SYSTEM_PROMPT_LEAKAGE = "System_prompt_leakage"
    SECURITY_VIOLATION = "Security_violation"
    SUSPICIOUS = "Suspicious"
    UNAUTHORIZED_ACTION = "Unauthorized_action"


class StabilityObservation(Enum):
    OK = "OK"
    TIMEOUT = "Timeout"
    ERROR = "Error"
    RETRY = "Retry"
    INCONSISTENT = "Inconsistent_behavior"


@dataclass
class TestCase:
    """Test case definition"""
    test_case_id: str
    feature_area: str
    description_vn: str
    user_message_input: str
    precondition: str
    expected_bot_response: str
    expected_parsed_transaction: Optional[Dict[str, Any]] = None
    target_dimensions_classs: List[str] = field(default_factory=list)
    target_owasp_risks: List[str] = field(default_factory=list)
    target_class_principles: List[str] = field(default_factory=list)
    priority: str = "Medium"
    severity_if_failed: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestCase":
        return cls(
            test_case_id=data.get("Test_Case_ID", ""),
            feature_area=data.get("Feature_Area", ""),
            description_vn=data.get("Description_VN", ""),
            user_message_input=data.get("User_Message_Input", ""),
            precondition=data.get("Precondition", ""),
            expected_bot_response=data.get("Expected_Bot_Response", ""),
            expected_parsed_transaction=data.get("Expected_Parsed_Transaction"),
            target_dimensions_classs=data.get("Target_Dimensions_CLASSS", []),
            target_owasp_risks=data.get("Target_OWASP_Risks", []),
            target_class_principles=data.get("Target_CLASS_Principles", []),
            priority=data.get("Priority", "Medium"),
            severity_if_failed=data.get("Severity_if_Failed")
        )


@dataclass
class ParsedTransaction:
    """Parsed transaction from bot response"""
    transaction_type: Optional[str] = None  # expense/income/transfer
    amount: Optional[float] = None
    currency: str = "VND"
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    transaction_date: Optional[str] = None
    description: Optional[str] = None
    member_id: Optional[str] = None
    display_name: Optional[str] = None
    confidence: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "currency": self.currency,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "transaction_date": self.transaction_date,
            "description": self.description,
            "member_id": self.member_id,
            "display_name": self.display_name,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParsedTransaction":
        if not data:
            return cls()
        return cls(
            transaction_type=data.get("transaction_type"),
            amount=data.get("amount"),
            currency=data.get("currency", "VND"),
            category_id=data.get("category_id"),
            category_name=data.get("category_name"),
            transaction_date=data.get("transaction_date"),
            description=data.get("description"),
            member_id=data.get("member_id"),
            display_name=data.get("display_name"),
            confidence=data.get("confidence")
        )


@dataclass
class TestRunResult:
    """Result of a single test run"""
    test_run_id: str
    test_case_id: str
    date: str
    tester: str = "LLM_Test_Agent"
    environment: str = "Staging"
    llm_model: str = "gpt-4o-mini"
    
    # Response data
    actual_bot_response: str = ""
    actual_parsed_transaction: Optional[Dict[str, Any]] = None
    
    # Result
    pass_fail: PassFailStatus = PassFailStatus.SKIP
    issues_found: bool = False
    issue_ids: str = ""
    
    # Metrics
    measured_latency_ms: int = 0
    measured_cost_vnd: float = 0.0
    token_usage: Optional[Dict[str, int]] = None
    accuracy_score_percent: float = 0.0
    
    # Observations
    security_observation: SecurityObservation = SecurityObservation.OK
    stability_observation: StabilityObservation = StabilityObservation.OK
    
    # Notes
    notes: str = ""
    class_principles_check: Optional[Dict[str, bool]] = None
    owasp_check: Optional[Dict[str, str]] = None
    
    # Raw data
    raw_request: Optional[Dict[str, Any]] = None
    raw_response: Optional[Dict[str, Any]] = None
    
    @staticmethod
    def generate_run_id() -> str:
        """Generate unique test run ID"""
        now = datetime.now()
        return f"RUN_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "Test_Run_ID": self.test_run_id,
            "Test_Case_ID": self.test_case_id,
            "Date": self.date,
            "Tester": self.tester,
            "Environment": self.environment,
            "LLM_Model": self.llm_model,
            "Actual_Bot_Response": self.actual_bot_response if self.actual_bot_response else "",  # Full response - no truncation for accurate parsing
            "Actual_Parsed_Transaction": json.dumps(self.actual_parsed_transaction) if self.actual_parsed_transaction else "",
            "Pass_Fail": self.pass_fail.value,
            "Issues_Found": "Yes" if self.issues_found else "No",
            "Issue_IDs": self.issue_ids,
            "Measured_Latency_ms": self.measured_latency_ms,
            "Measured_Cost_VND": round(self.measured_cost_vnd, 2),
            "Token_Usage": json.dumps(self.token_usage) if self.token_usage else "",
            "Accuracy_Score_percent": round(self.accuracy_score_percent, 2),
            "Security_Observation": self.security_observation.value,
            "Stability_Observation": self.stability_observation.value,
            "Notes": self.notes,
            "CLASS_Principles_Check": json.dumps(self.class_principles_check) if self.class_principles_check else "",
            "OWASP_Check": json.dumps(self.owasp_check) if self.owasp_check else ""
        }
    
    def to_log_json(self) -> Dict[str, Any]:
        """Full JSON for logging"""
        result = self.to_dict()
        result["Raw_Request"] = self.raw_request
        result["Raw_Response"] = self.raw_response
        result["Full_Bot_Response"] = self.actual_bot_response
        return result


@dataclass
class TestSummary:
    """Summary of test run"""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    partial: int = 0
    skipped: int = 0
    errors: int = 0
    
    avg_latency_ms: float = 0.0
    total_cost_vnd: float = 0.0
    avg_accuracy: float = 0.0
    
    security_issues: int = 0
    stability_issues: int = 0
    
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "Total_Tests": self.total_tests,
            "Passed": self.passed,
            "Failed": self.failed,
            "Partial": self.partial,
            "Skipped": self.skipped,
            "Errors": self.errors,
            "Pass_Rate_Percent": round(self.pass_rate(), 2),
            "Avg_Latency_ms": round(self.avg_latency_ms, 2),
            "Total_Cost_VND": round(self.total_cost_vnd, 2),
            "Avg_Accuracy_Percent": round(self.avg_accuracy, 2),
            "Security_Issues": self.security_issues,
            "Stability_Issues": self.stability_issues,
            "Duration_Seconds": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
        }
