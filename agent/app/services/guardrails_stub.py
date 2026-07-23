"""
Guardrails Passthrough Stub for US-011 / US-024.
"""

import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class GuardrailsClient:
    """Stub guardrails client logging passthrough events for PI-1 MVP."""

    async def validate(self, input_text: str) -> Tuple[str, List[str]]:
        """Validates input text and returns sanitized text + guardrail flags."""
        logger.info("guardrails: passthrough validation")
        return input_text, []
