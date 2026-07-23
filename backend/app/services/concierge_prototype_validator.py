"""
Concierge Prototype Validator & Assessment Service (US-003).

Validates concierge prototype results, user trust ratings, usefulness scores,
and preference percentages against US-003 Acceptance Criteria, Gate 0 thresholds, and NFR-003 (Privacy).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class PrototypeAssessmentStatus(str, Enum):
    VALID = "valid"
    INSUFFICIENT_QUESTIONS = "insufficient_questions"
    LOW_TRUSTWORTHINESS = "low_trustworthiness"
    LOW_PREFERENCE_RATE = "low_preference_rate"
    PII_ANONYMISATION_FAILED = "pii_anonymisation_failed"
    UNAPPROVED_SPONSOR = "unapproved_sponsor"


@dataclass
class QuestionEvaluation:
    question_id: str
    category: str
    question_text: str
    source_consulted: str
    cited_evidence: str
    trustworthiness_score: int  # 1-5 scale
    usefulness_score: int       # 1-5 scale
    preferred_over_current_method: bool
    user_feedback: Optional[str] = None


@dataclass
class ConciergePrototypeReport:
    prototype_id: str
    version: str
    date_executed: str
    pilot_business_unit: str
    sponsor_name: str
    sponsor_signed_off: bool
    total_questions_evaluated: int
    evaluated_questions: List[QuestionEvaluation] = field(default_factory=list)
    anonymised: bool = True
    pii_redacted: bool = True


@dataclass
class PrototypeValidationResult:
    status: PrototypeAssessmentStatus
    passed: bool
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metrics_summary: Optional[Dict] = None


class ConciergePrototypeValidator:
    """Validates US-003 concierge prototype session data against business acceptance criteria."""

    MIN_QUESTIONS = 10
    MIN_TRUSTWORTHINESS_HIGH_SCORE = 4
    MIN_TRUSTWORTHINESS_PERCENTAGE = 60.0  # >= 60% must score >= 4/5
    MIN_PREFERENCE_PERCENTAGE = 50.0       # >= 50% must prefer over current method

    def validate_prototype_report(self, report: ConciergePrototypeReport) -> PrototypeValidationResult:
        warnings: List[str] = []
        errors: List[str] = []

        # 1. Sponsor sign-off check
        if not report.sponsor_signed_off:
            errors.append(f"Concierge prototype report lacks formal sign-off from pilot sponsor {report.sponsor_name}.")

        # 2. NFR-003 Privacy check
        if not report.anonymised or not report.pii_redacted:
            errors.append("Report fails NFR-003 privacy requirements: PII redaction or anonymisation boolean is False.")

        # Check for un-anonymised emails/names in question_text or feedback
        for q in report.evaluated_questions:
            if "@" in q.question_text:
                errors.append(f"Question '{q.question_id}' appears to contain non-anonymised email in question text.")

        # 3. Minimum Question Count
        if report.total_questions_evaluated < self.MIN_QUESTIONS:
            errors.append(
                f"Concierge prototype requires at least {self.MIN_QUESTIONS} evaluated questions (found {report.total_questions_evaluated})."
            )

        if len(report.evaluated_questions) < report.total_questions_evaluated:
            warnings.append(
                f"Evaluated questions array length ({len(report.evaluated_questions)}) is less than total_questions_evaluated ({report.total_questions_evaluated})."
            )

        # Calculate metrics over evaluated questions
        total_q = len(report.evaluated_questions)
        if total_q == 0:
            errors.append("No evaluated question details provided.")
            return PrototypeValidationResult(
                status=PrototypeAssessmentStatus.INSUFFICIENT_QUESTIONS,
                passed=False,
                errors=errors,
            )

        high_trust_count = sum(1 for q in report.evaluated_questions if q.trustworthiness_score >= self.MIN_TRUSTWORTHINESS_HIGH_SCORE)
        preference_count = sum(1 for q in report.evaluated_questions if q.preferred_over_current_method)

        trustworthiness_pct = (high_trust_count / total_q) * 100.0
        preference_pct = (preference_count / total_q) * 100.0
        avg_trust = sum(q.trustworthiness_score for q in report.evaluated_questions) / total_q
        avg_usefulness = sum(q.usefulness_score for q in report.evaluated_questions) / total_q

        # 4. Acceptance Criteria: Trustworthiness Score (>=60% score >=4)
        if trustworthiness_pct < self.MIN_TRUSTWORTHINESS_PERCENTAGE:
            errors.append(
                f"Trustworthiness score target failed: {trustworthiness_pct:.1f}% scored >=4/5 (required >= {self.MIN_TRUSTWORTHINESS_PERCENTAGE:.1f}%)."
            )

        # 5. Acceptance Criteria: User Preference Rate (>=50% prefer concierge)
        if preference_pct < self.MIN_PREFERENCE_PERCENTAGE:
            warnings.append(
                f"Low preference rate detected: {preference_pct:.1f}% preferred concierge over current method (required >= {self.MIN_PREFERENCE_PERCENTAGE:.1f}%). Scope pivot may be needed."
            )
            if preference_pct < 40.0:  # Critical failure if under 40%
                errors.append(f"Preference rate severely low ({preference_pct:.1f}%). Gate 0 solution fit failed.")

        # 6. Check for missing citations in answers
        for q in report.evaluated_questions:
            if not q.cited_evidence or q.cited_evidence.strip() == "":
                errors.append(f"Question '{q.question_id}' was delivered to user without citation evidence.")

        is_passed = len(errors) == 0

        status = PrototypeAssessmentStatus.VALID if is_passed else PrototypeAssessmentStatus.UNAPPROVED_SPONSOR
        if not is_passed and any("NFR-003" in e or "email" in e for e in errors):
            status = PrototypeAssessmentStatus.PII_ANONYMISATION_FAILED
        elif not is_passed and any("Trustworthiness" in e for e in errors):
            status = PrototypeAssessmentStatus.LOW_TRUSTWORTHINESS
        elif not is_passed and any("Preference rate" in e for e in errors):
            status = PrototypeAssessmentStatus.LOW_PREFERENCE_RATE
        elif not is_passed and any("questions" in e.lower() for e in errors):
            status = PrototypeAssessmentStatus.INSUFFICIENT_QUESTIONS

        summary = {
            "total_questions": total_q,
            "trustworthiness_pct": round(trustworthiness_pct, 1),
            "preference_pct": round(preference_pct, 1),
            "average_trustworthiness_score": round(avg_trust, 2),
            "average_usefulness_score": round(avg_usefulness, 2),
            "gate_0_criteria_met": is_passed,
        }

        return PrototypeValidationResult(
            status=status,
            passed=is_passed,
            warnings=warnings,
            errors=errors,
            metrics_summary=summary,
        )
