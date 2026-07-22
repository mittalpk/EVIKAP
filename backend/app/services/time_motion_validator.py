"""
Time-Motion Baseline Validator & Analysis Module (US-002).

Validates time-motion survey results, interview metrics, fragmentation-cost figures,
and question-type distribution against US-002 Acceptance Criteria and NFR-003 (Privacy/PII).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AssessmentStatus(str, Enum):
    VALID = "valid"
    INSUFFICIENT_SAMPLE_SIZE = "insufficient_sample_size"
    LOW_FRAGMENTATION_WARNING = "low_fragmentation_warning"
    FAST_TIME_TO_ANSWER_WARNING = "fast_time_to_answer_warning"
    PII_ANONYMISATION_FAILED = "pii_anonymisation_failed"
    INVALID_QUESTION_TYPES = "invalid_question_types"
    UNAPPROVED_SPONSOR = "unapproved_sponsor"


@dataclass
@dataclass
class QuestionTypeMetric:
    id: str
    question_type: str
    median_time_to_answer_minutes: float
    mean_systems_consulted: float
    primary_systems_consulted: List[str] = field(default_factory=list)


@dataclass
@dataclass
class AnonymisedInterviewNote:
    participant_id: str
    role: str
    key_quote: str
    reported_daily_search_hours: float
    avg_systems_used: float


@dataclass
class TimeMotionBaselineReport:
    baseline_id: str
    version: str
    date_published: str
    pilot_business_unit: str
    sponsor_name: str
    sponsor_signed_off: bool
    interviews_completed: int
    survey_responses_collected: int
    overall_median_time_to_answer_minutes: float
    overall_avg_systems_consulted: float
    question_types: List[QuestionTypeMetric] = field(default_factory=list)
    top_10_question_types: List[Dict[str, str]] = field(default_factory=list)
    interview_notes: List[AnonymisedInterviewNote] = field(default_factory=list)
    anonymised: bool = True
    pii_redacted: bool = True


@dataclass
class BaselineValidationResult:
    status: AssessmentStatus
    passed: bool
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metrics_summary: Optional[Dict] = None


class TimeMotionBaselineValidator:
    """Validates US-002 baseline research data against business acceptance criteria and NFR-003."""

    MIN_INTERVIEWS = 5
    MIN_SURVEY_RESPONSES = 10
    MIN_QUESTION_TYPES = 3
    MIN_FRAGMENTATION_THRESHOLD = 2.0
    MIN_TIME_TO_ANSWER_THRESHOLD = 5.0

    def validate_baseline_report(self, report: TimeMotionBaselineReport) -> BaselineValidationResult:
        warnings: List[str] = []
        errors: List[str] = []

        # 1. Check Sponsor Sign-off
        if not report.sponsor_signed_off:
            errors.append(f"Baseline report lacks formal sign-off from pilot sponsor {report.sponsor_name}.")

        # 2. Check NFR-003 Privacy & Anonymisation
        if not report.anonymised or not report.pii_redacted:
            errors.append("Report fails NFR-003 privacy requirements: PII redaction or anonymisation boolean is False.")

        # Check for un-anonymised participant IDs (e.g. real names or emails in participant_id)
        for note in report.interview_notes:
            if "@" in note.participant_id or " " in note.participant_id:
                errors.append(f"Participant ID '{note.participant_id}' appears to contain non-anonymised identifier.")

        # 3. Sample Size Thresholds & Edge Cases
        if report.interviews_completed < self.MIN_INTERVIEWS:
            warnings.append(
                f"Interviews completed ({report.interviews_completed}) is below recommended target of {self.MIN_INTERVIEWS}. Proceeding with confidence caveat."
            )
        if report.survey_responses_collected < self.MIN_SURVEY_RESPONSES:
            warnings.append(
                f"Survey responses ({report.survey_responses_collected}) is below target of {self.MIN_SURVEY_RESPONSES}. Proceeding with confidence caveat."
            )

        # 4. Question Types Baseline
        if len(report.question_types) < self.MIN_QUESTION_TYPES:
            errors.append(
                f"At least {self.MIN_QUESTION_TYPES} question types must have published time-to-answer metrics (found {len(report.question_types)})."
            )

        if len(report.top_10_question_types) < 10:
            errors.append(f"Top 10 question types list is incomplete (found {len(report.top_10_question_types)}).")

        # 5. Low Fragmentation Edge Case Check (< 2 systems per question)
        if report.overall_avg_systems_consulted < self.MIN_FRAGMENTATION_THRESHOLD:
            warnings.append(
                f"Low fragmentation detected: average systems consulted ({report.overall_avg_systems_consulted:.1f}) is below {self.MIN_FRAGMENTATION_THRESHOLD}. Scope may be too narrow."
            )

        # 6. Fast Time-to-Answer Edge Case Check (< 5 minutes)
        if report.overall_median_time_to_answer_minutes < self.MIN_TIME_TO_ANSWER_THRESHOLD:
            warnings.append(
                f"Median time-to-answer ({report.overall_median_time_to_answer_minutes:.1f}m) is below {self.MIN_TIME_TO_ANSWER_THRESHOLD}m threshold. Question selection may be unrepresentative."
            )

        is_passed = len(errors) == 0

        status = AssessmentStatus.VALID if is_passed else AssessmentStatus.UNAPPROVED_SPONSOR
        if not is_passed and any("NFR-003" in e for e in errors):
            status = AssessmentStatus.PII_ANONYMISATION_FAILED
        elif not is_passed and any("question types" in e.lower() for e in errors):
            status = AssessmentStatus.INVALID_QUESTION_TYPES

        summary = {
            "median_time_to_answer_minutes": report.overall_median_time_to_answer_minutes,
            "avg_systems_consulted": report.overall_avg_systems_consulted,
            "interviews_count": report.interviews_completed,
            "survey_count": report.survey_responses_collected,
            "question_types_count": len(report.question_types),
            "top_question_types_count": len(report.top_10_question_types),
        }

        return BaselineValidationResult(
            status=status,
            passed=is_passed,
            warnings=warnings,
            errors=errors,
            metrics_summary=summary,
        )
