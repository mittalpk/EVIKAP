"""
Test suite for US-002 Time-Motion Survey & Knowledge Fragmentation Baseline Validator.
Validates happy path baseline data, missing sponsor sign-off, NFR-003 privacy checks,
insufficient sample size, low fragmentation warning, fast time-to-answer edge cases, and incomplete question types.
Uses workspace-root imports: `from backend.app.services.time_motion_validator import ...`
"""

import pytest

from backend.app.services.time_motion_validator import (
    AnonymisedInterviewNote,
    AssessmentStatus,
    QuestionTypeMetric,
    TimeMotionBaselineReport,
    TimeMotionBaselineValidator,
)


@pytest.fixture
def valid_baseline_report():
    return TimeMotionBaselineReport(
        baseline_id="BASELINE-PI0-US002",
        version="1.0",
        date_published="2026-07-22",
        pilot_business_unit="Digital Services & Engineering",
        sponsor_name="Jane Doe",
        sponsor_signed_off=True,
        interviews_completed=6,
        survey_responses_collected=14,
        overall_median_time_to_answer_minutes=27.5,
        overall_avg_systems_consulted=3.8,
        anonymised=True,
        pii_redacted=True,
        question_types=[
            QuestionTypeMetric("QT-01", "Architecture patterns", 35.0, 4.2, ["Confluence", "GitHub"]),
            QuestionTypeMetric("QT-02", "Deployment procedures", 25.0, 3.6, ["Wiki", "K8s Helm"]),
            QuestionTypeMetric("QT-03", "API specs", 22.5, 3.5, ["GitHub", "Swagger"]),
        ],
        top_10_question_types=[
            {"rank": "1", "category": "Architecture patterns"},
            {"rank": "2", "category": "API specs"},
            {"rank": "3", "category": "Deployment procedures"},
            {"rank": "4", "category": "Database schema definitions"},
            {"rank": "5", "category": "Environment configuration"},
            {"rank": "6", "category": "Auth/RBAC token scope"},
            {"rank": "7", "category": "Incident response runbooks"},
            {"rank": "8", "category": "Third-party SDK integration"},
            {"rank": "9", "category": "Observability standards"},
            {"rank": "10", "category": "CI/CD troubleshooting"},
        ],
        interview_notes=[
            AnonymisedInterviewNote("P01", "Senior Engineer", "Takes 30m to find API specs", 2.0, 4.0),
            AnonymisedInterviewNote("P02", "Tech Lead", "Slack DMs about arch decisions", 2.5, 5.0),
        ],
    )


def test_valid_baseline_report(valid_baseline_report):
    validator = TimeMotionBaselineValidator()
    res = validator.validate_baseline_report(valid_baseline_report)

    assert res.passed is True
    assert res.status == AssessmentStatus.VALID
    assert len(res.errors) == 0
    assert len(res.warnings) == 0
    assert res.metrics_summary["median_time_to_answer_minutes"] == 27.5
    assert res.metrics_summary["avg_systems_consulted"] == 3.8


def test_edge_case_missing_sponsor_signoff(valid_baseline_report):
    valid_baseline_report.sponsor_signed_off = False
    validator = TimeMotionBaselineValidator()
    res = validator.validate_baseline_report(valid_baseline_report)

    assert res.passed is False
    assert res.status == AssessmentStatus.UNAPPROVED_SPONSOR
    assert any("lacks formal sign-off" in err for err in res.errors)


def test_edge_case_nfr003_pii_anonymisation_failure(valid_baseline_report):
    valid_baseline_report.pii_redacted = False
    validator = TimeMotionBaselineValidator()
    res = validator.validate_baseline_report(valid_baseline_report)

    assert res.passed is False
    assert res.status == AssessmentStatus.PII_ANONYMISATION_FAILED
    assert any("NFR-003" in err for err in res.errors)


def test_edge_case_non_anonymised_participant_id(valid_baseline_report):
    valid_baseline_report.interview_notes.append(
        AnonymisedInterviewNote("john.doe@example.com", "Engineer", "Leaked email", 1.0, 2.0)
    )
    validator = TimeMotionBaselineValidator()
    res = validator.validate_baseline_report(valid_baseline_report)

    assert res.passed is False
    assert any("Participant ID 'john.doe@example.com'" in err for err in res.errors)


def test_edge_case_insufficient_sample_size_warnings(valid_baseline_report):
    valid_baseline_report.interviews_completed = 3
    valid_baseline_report.survey_responses_collected = 7
    validator = TimeMotionBaselineValidator()
    res = validator.validate_baseline_report(valid_baseline_report)

    # Warnings do not fail validation unless errors exist
    assert res.passed is True
    assert len(res.warnings) == 2
    assert any("Interviews completed (3)" in w for w in res.warnings)
    assert any("Survey responses (7)" in w for w in res.warnings)


def test_edge_case_low_fragmentation_warning(valid_baseline_report):
    valid_baseline_report.overall_avg_systems_consulted = 1.5
    validator = TimeMotionBaselineValidator()
    res = validator.validate_baseline_report(valid_baseline_report)

    assert res.passed is True
    assert any("Low fragmentation detected" in w for w in res.warnings)


def test_edge_case_fast_time_to_answer_warning(valid_baseline_report):
    valid_baseline_report.overall_median_time_to_answer_minutes = 3.5
    validator = TimeMotionBaselineValidator()
    res = validator.validate_baseline_report(valid_baseline_report)

    assert res.passed is True
    assert any("Median time-to-answer (3.5m) is below 5.0m threshold" in w for w in res.warnings)


def test_edge_case_incomplete_question_types(valid_baseline_report):
    valid_baseline_report.question_types = valid_baseline_report.question_types[:2]  # only 2
    valid_baseline_report.top_10_question_types = valid_baseline_report.top_10_question_types[:8]  # only 8
    validator = TimeMotionBaselineValidator()
    res = validator.validate_baseline_report(valid_baseline_report)

    assert res.passed is False
    assert res.status == AssessmentStatus.INVALID_QUESTION_TYPES
    assert any("At least 3 question types" in err for err in res.errors)
    assert any("Top 10 question types list is incomplete" in err for err in res.errors)
