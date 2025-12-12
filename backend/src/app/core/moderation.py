"""
Content moderation service.

Provides automated content filtering to detect and block illegal or prohibited items
from being listed on the marketplace. Uses keyword-based detection with regex patterns
for high-precision matching of banned content.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import ClassVar

logger = logging.getLogger(__name__)


@dataclass
class ModerationResult:
    """Result of content moderation check."""

    is_violation: bool
    matched_terms: list[str]
    reason: str | None = None


class ContentModerator:
    """
    Automated content moderation service.

    Scans text content for illegal items, prohibited goods, and policy violations
    using keyword matching and regex patterns. Designed to prevent marketplace abuse
    while minimizing false positives.
    """

    # Maximum number of matched terms to show in error message
    MAX_TERMS_IN_MESSAGE: ClassVar[int] = 3

    # Weapons and Dangerous Items
    WEAPONS_KEYWORDS: ClassVar[set[str]] = {
        "gun",
        "guns",
        "firearm",
        "firearms",
        "rifle",
        "rifles",
        "pistol",
        "pistols",
        "handgun",
        "handguns",
        "weapon",
        "weapons",
        "ammunition",
        "ammo",
        "explosive",
        "explosives",
        "grenade",
        "grenades",
        "bomb",
        "bombs",
        "knife sale",  # "knife" alone triggers on "pocket knife holder"
        "switchblade",
        "brass knuckles",
        "nunchucks",
        "taser",
        "stun gun",
        "pepper spray sale",
    }

    # Controlled Substances and Drugs
    DRUGS_KEYWORDS: ClassVar[set[str]] = {
        "drug",
        "drugs",
        "narcotics",
        "narcotic",
        "illegal substance",
        "controlled substance",
        # Hard drugs
        "cocaine",
        "heroin",
        "methamphetamine",
        "meth",
        "fentanyl",
        "opioid",
        "opioids",
        "opiate",
        "opiates",
        # Prescription drugs (commonly abused)
        "prescription drug",
        "xanax",
        "adderall",
        "ritalin",
        "vyvanse",
        "concerta",
        "klonopin",
        "valium",
        "ativan",
        "ambien",
        "percocet",
        "oxycontin",
        "vicodin",
        "codeine",
        "tramadol",
        "viagra",
        "cialis",
        # Performance enhancing
        "steroid",
        "steroids",
        "hgh",
        "human growth hormone",
        # Cannabis (where illegal)
        "marijuana",
        "weed",
        "cannabis",
        "pot",
        "edibles",
        "thc",
        "cbd oil",
        # Alcohol (underage concerns)
        "alcohol",
        "beer",
        "liquor",
        "vodka",
        "whiskey",
        "wine",
        "spirits",
        "booze",
        # Study drugs / nootropics
        "modafinil",
        "nootropic",
        "smart drug",
    }

    # Counterfeit and Fraudulent Items
    COUNTERFEIT_KEYWORDS: ClassVar[set[str]] = {
        "fake id",
        "counterfeit",
        "replica designer",
        "knock off",
        "bootleg",
        "pirated",
        "cracked software",
        "hacked account",
        "stolen",
        "forged",
    }

    # Personal Information and Identity Theft
    IDENTITY_KEYWORDS: ClassVar[set[str]] = {
        "ssn",
        "social security number",
        "passport scan",
        "driver license scan",
        "credit card number",
        "bank account number",
        "cvv",
        "fullz",  # Dark web term for complete identity info
        "identity document",
        "fake identity",
    }

    # Illegal Services
    ILLEGAL_SERVICES: ClassVar[set[str]] = {
        "illegal items",
        "illegal goods",
        "illegal sale",
        "illegal selling",
        "hacking service",
        "hitman",
        "assassination",
        "money laundering",
        "tax evasion",
        "fake degree",
        "essay writing service",  # Academic dishonesty
        "paper mill",
    }

    # Adult Content and Human Trafficking
    ADULT_KEYWORDS: ClassVar[set[str]] = {
        "escort",
        "prostitution",
        "sex work",
        "massage parlor",  # Context-dependent
        "happy ending",
        "adult services",
    }

    # Endangered Species and Illegal Animal Trade
    ANIMAL_KEYWORDS: ClassVar[set[str]] = {
        "ivory",
        "rhino horn",
        "tiger bone",
        "endangered species",
        "exotic pet illegal",
    }

    # Combine all keyword sets
    BANNED_KEYWORDS = (
        WEAPONS_KEYWORDS
        | DRUGS_KEYWORDS
        | COUNTERFEIT_KEYWORDS
        | IDENTITY_KEYWORDS
        | ILLEGAL_SERVICES
        | ADULT_KEYWORDS
        | ANIMAL_KEYWORDS
    )

    # Regex patterns for additional detection
    PATTERNS: ClassVar[list[re.Pattern[str]]] = [
        # SSN format: 123-45-6789
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b", re.IGNORECASE),
        # Credit card patterns (simplified)
        re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", re.IGNORECASE),
        # "4 sale" drug patterns
        re.compile(r"\b(pills?|drugs?|narcotics?)\s+(for|4)\s+sale\b", re.IGNORECASE),
        # Common drug slang
        re.compile(
            r"\b(molly|ecstasy|mdma|lsd|acid|shrooms|DMT|ketamine|crack)\s+(for|4)?\s*sale\b",
            re.IGNORECASE,
        ),
    ]

    def check_content(self, title: str, description: str) -> ModerationResult:
        """
        Check listing content for policy violations.

        Scans both title and description for banned keywords and suspicious patterns.
        Uses case-insensitive matching with word boundaries to reduce false positives.

        Args:
            title: Listing title
            description: Listing description

        Returns:
            ModerationResult: Contains violation status, matched terms, and reason
        """
        # Combine and normalize text
        combined_text = f"{title} {description}".lower()

        # Check for banned keywords
        matched_keywords = []
        for keyword in self.BANNED_KEYWORDS:
            # Use word boundaries to avoid false positives (e.g., "gun" in "begun")
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, combined_text, re.IGNORECASE):
                matched_keywords.append(keyword)

        # Check regex patterns
        matched_patterns = [
            pattern.pattern for pattern in self.PATTERNS if pattern.search(combined_text)
        ]

        # Determine result
        is_violation = bool(matched_keywords or matched_patterns)

        if is_violation:
            all_matches = matched_keywords + matched_patterns
            reason = (
                f"Content policy violation: Detected prohibited content - {', '.join(all_matches[: self.MAX_TERMS_IN_MESSAGE])}"
                + (
                    f" and {len(all_matches) - self.MAX_TERMS_IN_MESSAGE} more"
                    if len(all_matches) > self.MAX_TERMS_IN_MESSAGE
                    else ""
                )
            )
            logger.warning(
                "Content moderation violation detected",
                extra={
                    "title": title[:100],
                    "matched_terms": all_matches,
                },
            )
        else:
            reason = None

        return ModerationResult(
            is_violation=is_violation,
            matched_terms=matched_keywords + matched_patterns,
            reason=reason,
        )


# Create singleton instance
content_moderator = ContentModerator()
