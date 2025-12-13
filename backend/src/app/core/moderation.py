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
        # Generic terms
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
        # Popular firearm models
        "glock",
        "glock 17",
        "glock 19",
        "sig sauer",
        "smith wesson",
        "beretta",
        "colt 1911",
        "ar-15",
        "ar15",
        "ak-47",
        "ak47",
        "remington",
        "ruger",
        "springfield",
        "mossberg",
        "winchester",
        # Explosives
        "explosive",
        "explosives",
        "grenade",
        "grenades",
        "bomb",
        "bombs",
        # Other weapons
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
        # Alcohol (underage concerns) - use specific sale/transfer phrases to avoid overblocking collectibles and paraphernalia
        "alcohol for sale",
        "selling alcohol",
        "beer for sale",
        "selling beer",
        "vodka for sale",
        "selling vodka",
        "whiskey for sale",
        "selling whiskey",
        "wine for sale",
        "selling wine",
        "liquor for sale",
        "selling liquor",
        "spirits for sale",
        "selling spirits",
        "booze for sale",
        "selling booze",
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
        "paper mill",
    }

    # Adult Content and Human Trafficking
    ADULT_KEYWORDS: ClassVar[set[str]] = {
        "escort",
        "prostitution",
        "sex work",
        # "massage parlor",  # Removed: Context-dependent, can flag legitimate businesses
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
        # External marketplace URLs (suspicious)
        re.compile(
            r"(https?://|www\.)?(craigslist\.org|facebook\.com/marketplace|offerup\.com|letgo\.com|mercari\.com)(/[^\s]*)?",
            re.IGNORECASE,
        ),
    ]

    @staticmethod
    def _normalize_evasion(text: str) -> str:
        """
        Normalize common evasion techniques.

        Handles leet speak (c0caine), spacing (g u n s), and special characters.

        Args:
            text: Input text to normalize

        Returns:
            str: Normalized text with evasion patterns converted to standard form
        """
        # Convert to lowercase first
        text = text.lower()

        # Common leet speak substitutions
        leet_map = {
            "0": "o",
            "1": "i",
            "3": "e",
            "4": "a",
            "5": "s",
            "7": "t",
            "8": "b",
            "9": "g",
            "@": "a",
            "$": "s",
        }
        for leet, normal in leet_map.items():
            text = text.replace(leet, normal)

        # Remove common separator characters (but keep regular spaces for now)
        text = text.replace("_", "").replace("-", "").replace(".", "")

        # Remove excessive spaces (more than one space becomes one space)
        return " ".join(text.split())

    def check_content(self, title: str, description: str) -> ModerationResult:
        """
        Check listing content for policy violations.

        Scans both title and description for banned keywords and suspicious patterns.
        Uses case-insensitive matching with word boundaries to reduce false positives.
        Includes evasion detection for common obfuscation techniques.

        Args:
            title: Listing title
            description: Listing description

        Returns:
            ModerationResult: Contains violation status, matched terms, and reason
        """
        # Combine text
        combined_text = f"{title} {description}".lower()

        # Also check normalized version to catch evasion attempts
        normalized_text = self._normalize_evasion(combined_text)

        # Check for banned keywords in both original and normalized text
        matched_keywords = []
        for keyword in self.BANNED_KEYWORDS:
            # Use word boundaries to avoid false positives (e.g., "gun" in "begun")
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, combined_text, re.IGNORECASE) or re.search(
                pattern, normalized_text, re.IGNORECASE
            ):
                matched_keywords.append(keyword)

        # Check regex patterns
        matched_patterns = [
            pattern.pattern
            for pattern in self.PATTERNS
            if pattern.search(combined_text) or pattern.search(normalized_text)
        ]

        # Determine result
        is_violation = bool(matched_keywords or matched_patterns)

        if is_violation:
            all_matches = matched_keywords + matched_patterns
            # Deduplicate matches
            all_matches = list(dict.fromkeys(all_matches))

            reason = (
                f"Content policy violation: Detected prohibited content - {', '.join(all_matches[: self.MAX_TERMS_IN_MESSAGE])}"
                + (
                    f" and {len(all_matches) - self.MAX_TERMS_IN_MESSAGE} more"
                    if len(all_matches) > self.MAX_TERMS_IN_MESSAGE
                    else ""
                )
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
