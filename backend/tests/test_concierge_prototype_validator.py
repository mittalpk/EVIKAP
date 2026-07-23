"""
Test suite for US-003 Concierge Prototype Validator and Gate 0 criteria validation.
Covers valid concierge prototype report, missing sponsor sign-off, NFR-003 privacy checks,
insufficient question count, low trustworthiness score, low preference rate, and missing citations.
Uses workspace-root imports: `from backend.app.services.concierge_prototype_validator import ...`
"""

import pytest

from backend.app.services.concierge_prototype_validator import (
    ConciergePrototypeReport,
    ConciergePrototypeValidator,
    PrototypeAssessmentStatus,
    QuestionEvaluation,
)


@pytest.fixture
def valid_prototype_report():
    return ConciergePrototypeReport(
        prototype_id="CONCIERGE-PI0-US003",
        version="1.0",
        date_executed="2026-07-23",
        pilot_business_unit="Digital Services & Engineering",
        sponsor_name="Jane Doe",
        sponsor_signed_off=True,
        total_questions_evaluated=10,
        anonymised=True,
        pii_redacted=True,
        evaluated_questions=[
            QuestionEvaluation("Q-01", "Arch", "What is gRPC auth policy?", "Wiki", "ENG / Auth Policy", 5, 5, True),
            QuestionEvaluation("Q-02", "Arch", "Is raw JWT allowed?", "Wiki", "ENG / Security Baseline", 4, 4, True),
            QuestionEvaluation("Q-03", "Deploy", "Rollback steps?", "GitHub", "repo / runbook.md", 4, 4, True),
            QuestionEvaluation("Q-04", "Deploy", "Redis cache dependencies?", "GitHub", "values-prod.yaml", 5, 5, True),
            QuestionEvaluation("Q-05", "API", "Retry policy settings?", "GitHub", "retry.go", 4, 4, True),
            QuestionEvaluation("Q-06", "API", "Timeout override?", "GitHub", "client.go", 4, 4, True),
            QuestionEvaluation("Q-07", "DB", "User GUID max length?", "GitHub", "migration.sql", 4, 3, False),
            QuestionEvaluation("Q-08", "Config", "Staging KeyVault access?", "Wiki", "Access Guide", 4, 4, True),
            QuestionEvaluation("Q-09", "Auth", "RBAC audit log role?", "Wiki", "RBAC Matrix v4", 3, 3, False),
            QuestionEvaluation("Q-10", "Incident", "P1 DB lock SLA?", "Wiki", "On-Call Protocol", 5, 5, True),
        ],
    )


def test_valid_concierge_prototype_report(valid_prototype_report):
    validator = ConciergePrototypeValidator()
    res = validator.validate_prototype_report(valid_prototype_report)

    assert res.passed is True
    assert res.status == PrototypeAssessmentStatus.VALID
    assert len(res.errors) == 0
    assert res.metrics_summary["trustworthiness_pct"] == 90.0  # 9 out of 10 score >=4
    assert res.metrics_summary["preference_pct"] == 80.0       # 8 out of 10 prefer
    assert res.metrics_summary["gate_0_criteria_met"] is True


def test_edge_case_missing_sponsor_signoff(valid_prototype_report):
    valid_prototype_report.sponsor_signed_off = False
    validator = ConciergePrototypeValidator()
    res = validator.validate_prototype_report(valid_prototype_report)

    assert res.passed is False
    assert res.status == PrototypeAssessmentStatus.UNAPPROVED_SPONSOR
    assert any("lacks formal sign-off" in err for err in res.errors)


def test_edge_case_nfr003_pii_anonymisation_failure(valid_prototype_report):
    valid_prototype_report.pii_redacted = False
    validator = ConciergePrototypeValidator()
    res = validator.validate_prototype_report(valid_prototype_report)

    assert res.passed is False
    assert res.status == PrototypeAssessmentStatus.PII_ANONYMISATION_FAILED
    assert any("NFR-003" in err for err in res.errors)


def test_edge_case_un_anonymised_email_in_question(valid_prototype_report):
    valid_prototype_report.evaluated_questions[0].question_text = "What is john.doe@example.com's gRPC auth policy?"
    validator = ConciergePrototypeValidator()
    res = validator.validate_prototype_report(valid_prototype_report)

    assert res.passed is False
    assert any("non-anonymised email" in err for err in res.errors)


def test_edge_case_insufficient_question_count(valid_prototype_report):
    valid_prototype_report.total_questions_evaluated = 8
    valid_prototype_report.evaluated_questions = valid_prototype_report.evaluated_questions[:8]
    validator = ConciergePrototypeValidator()
    res = validator.validate_prototype_report(valid_prototype_report)

    assert res.passed is False
    assert res.status == PrototypeAssessmentStatus.INSUFFICIENT_QUESTIONS
    assert any("at least 10 evaluated questions" in err for err in res.errors)


def test_edge_case_low_trustworthiness_score(valid_prototype_report):
    # Change scores so only 5 out of 10 score >=4 (50% < 60% threshold)
    for q in valid_prototype_report.evaluated_questions[5:]:
        q.trustworthiness_score = 3

    validator = ConciergePrototypeValidator()
    res = validator.validate_prototype_report(valid_prototype_report)

    assert res.passed is False
    assert res.status == PrototypeAssessmentStatus.LOW_TRUSTWORTHINESS
    assert any("Trustworthiness score target failed" in err for err in res.errors)


def test_edge_case_low_preference_rate_warning_and_failure(valid_prototype_report):
    # 4 out of 10 prefer (40% < 50% threshold)
    for i, q in enumerate(valid_prototype_report.evaluated_questions):
        q.preferred_over_current_method = (i < 4)

    validator = ConciergePrototypeValidator()
    res = validator.validate_prototype_report(valid_prototype_report)

    assert res.passed is True  # warning issued if >= 40% but < 50%
    assert any("Low preference rate detected" in w for w in res.warnings)

    # If < 40%, severe failure
    for i, q in enumerate(valid_prototype_report.evaluated_questions):
        q.preferred_over_current_method = (i < 3)

    res_severe = validator.validate_prototype_report(valid_prototype_report)
    assert res_severe.passed is False
    assert res_severe.status == PrototypeAssessmentStatus.LOW_PREFERENCE_RATE
    assert any("Preference rate severely low" in err for err in res_severe.errors)


def test_edge_case_missing_citations(valid_prototype_report):
    valid_prototype_report.evaluated_questions[2].cited_evidence = ""
    validator = ConciergePrototypeValidator()
    res = validator.validate_prototype_report(valid_prototype_report)

    assert res.passed is False
    assert any("without citation evidence" in err for err in res.errors)
