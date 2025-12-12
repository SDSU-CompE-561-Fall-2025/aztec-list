"""Unit tests for ContentModerator."""

import pytest

from app.core.moderation import ContentModerator, ModerationResult


class TestContentModerator:
    """Tests for content moderation service."""

    @pytest.fixture
    def moderator(self):
        """Create ContentModerator instance."""
        return ContentModerator()

    def test_clean_content_passes(self, moderator):
        """Test that clean content passes moderation."""
        result = moderator.check_content(
            title="Used Laptop for Sale",
            description="Selling my gently used laptop. Great condition, works perfectly.",
        )

        assert result.is_violation is False
        assert result.matched_terms == []
        assert result.reason is None

    def test_weapons_keyword_detected(self, moderator):
        """Test that weapons keywords are detected."""
        result = moderator.check_content(
            title="Firearm for sale",
            description="Contact me for details",
        )

        assert result.is_violation is True
        assert "firearm" in result.matched_terms
        assert "prohibited content" in result.reason.lower()

    def test_drugs_keyword_detected(self, moderator):
        """Test that drug keywords are detected."""
        result = moderator.check_content(
            title="Quality product",
            description="Cocaine available, good price",
        )

        assert result.is_violation is True
        assert "cocaine" in result.matched_terms

    def test_college_drugs_detected(self, moderator):
        """Test that college/study drugs are detected."""
        test_cases = [
            ("Adderall for sale", "Contact for prices"),
            ("Ritalin available", "Study help"),
            ("Selling vodka", "College party supplies"),
            ("Beer for sale", "Get your drinks here"),
        ]

        for title, description in test_cases:
            result = moderator.check_content(title=title, description=description)
            assert result.is_violation is True, f"Failed to detect: {title}"

    def test_counterfeit_keyword_detected(self, moderator):
        """Test that counterfeit keywords are detected."""
        result = moderator.check_content(
            title="Designer Bag",
            description="Replica designer handbag, looks authentic",
        )

        assert result.is_violation is True
        assert "replica designer" in result.matched_terms

    def test_identity_theft_keyword_detected(self, moderator):
        """Test that identity theft keywords are detected."""
        result = moderator.check_content(
            title="Documents for sale",
            description="Fake ID available with hologram",
        )

        assert result.is_violation is True
        assert "fake id" in result.matched_terms

    def test_ssn_pattern_detected(self, moderator):
        """Test that SSN patterns are detected."""
        result = moderator.check_content(
            title="Info for sale",
            description="Contact info: 123-45-6789",
        )

        assert result.is_violation is True
        assert any("\\d{3}-\\d{2}-\\d{4}" in term for term in result.matched_terms)

    def test_credit_card_pattern_detected(self, moderator):
        """Test that credit card patterns are detected."""
        result = moderator.check_content(
            title="Card info",
            description="Payment: 4532-1234-5678-9010",
        )

        assert result.is_violation is True
        # Check for credit card pattern match
        assert len(result.matched_terms) > 0

    def test_drug_slang_pattern_detected(self, moderator):
        """Test that drug slang patterns are detected."""
        result = moderator.check_content(
            title="Party supplies",
            description="Molly for sale, best quality",
        )

        assert result.is_violation is True

    def test_multiple_violations(self, moderator):
        """Test that multiple violations are detected."""
        result = moderator.check_content(
            title="Special items",
            description="Selling guns, fake ID, and cocaine. Contact for prices.",
        )

        assert result.is_violation is True
        assert len(result.matched_terms) >= 3
        assert "gun" in result.matched_terms or "guns" in [t for t in result.matched_terms]

    def test_case_insensitive_matching(self, moderator):
        """Test that matching is case-insensitive."""
        result = moderator.check_content(
            title="FIREARM FOR SALE",
            description="Best GUN available",
        )

        assert result.is_violation is True

    def test_word_boundary_prevents_false_positives(self, moderator):
        """Test that word boundaries prevent false positives."""
        # "gun" should not match in "begun"
        result = moderator.check_content(
            title="Project begun yesterday",
            description="Work has begun on the new design",
        )

        assert result.is_violation is False

    def test_innocent_knife_mention_passes(self, moderator):
        """Test that innocent knife mentions pass (e.g., knife holder)."""
        result = moderator.check_content(
            title="Kitchen Knife Holder",
            description="Wooden knife block, holds 8 knives",
        )

        # "knife" alone is not banned, only "knife sale"
        assert result.is_violation is False

    def test_knife_sale_detected(self, moderator):
        """Test that knife sale is detected."""
        result = moderator.check_content(
            title="Knife sale",
            description="Selling combat knives",
        )

        assert result.is_violation is True
        assert "knife sale" in result.matched_terms

    def test_reason_truncates_long_match_list(self, moderator):
        """Test that reason message truncates long match lists."""
        # Create content with many violations
        result = moderator.check_content(
            title="Everything for sale",
            description="guns, cocaine, fake id, stolen goods, counterfeit, bomb, grenade",
        )

        assert result.is_violation is True
        assert "and" in result.reason or len(result.matched_terms) <= 3

    def test_empty_content(self, moderator):
        """Test that empty content passes."""
        result = moderator.check_content(title="", description="")

        assert result.is_violation is False

    def test_special_characters_handled(self, moderator):
        """Test that special characters in content are handled."""
        result = moderator.check_content(
            title="Item!!! @#$%",
            description="Special (chars) & symbols <test>",
        )

        assert result.is_violation is False

    def test_title_only_violation(self, moderator):
        """Test that violations in title only are detected."""
        result = moderator.check_content(
            title="Firearm available",
            description="Contact for info",
        )

        assert result.is_violation is True

    def test_description_only_violation(self, moderator):
        """Test that violations in description only are detected."""
        result = moderator.check_content(
            title="Item for sale",
            description="Selling my gun collection",
        )

        assert result.is_violation is True

    def test_illegal_services_detected(self, moderator):
        """Test that illegal services are detected."""
        result = moderator.check_content(
            title="Professional services",
            description="Offering hacking service for hire",
        )

        assert result.is_violation is True
        assert "hacking service" in result.matched_terms

    def test_endangered_species_detected(self, moderator):
        """Test that endangered species keywords are detected."""
        result = moderator.check_content(
            title="Rare item",
            description="Real ivory sculpture for sale",
        )

        assert result.is_violation is True
        assert "ivory" in result.matched_terms

    def test_generic_drug_term_detected(self, moderator):
        """Test that generic drug terms are detected (not just specific drugs)."""
        result = moderator.check_content(
            title="drugs",
            description="Various drugs available",
        )

        assert result.is_violation is True
        assert "drugs" in result.matched_terms

    def test_illegal_items_detected(self, moderator):
        """Test that generic 'illegal items' phrase is detected."""
        result = moderator.check_content(
            title="Great deals",
            description="selling my illegal items!",
        )

        assert result.is_violation is True
        assert "illegal items" in result.matched_terms

    def test_combined_generic_violation(self, moderator):
        """Test detection of multiple generic prohibited terms."""
        result = moderator.check_content(
            title="drugs",
            description="selling my illegal items!",
        )

        assert result.is_violation is True
        assert "drugs" in result.matched_terms

    def test_evasion_leet_speak(self, moderator):
        """Test detection of leet speak evasion (c0caine, w3apon)."""
        test_cases = [
            ("c0caine for sale", "Good price"),  # 0 -> o
            ("w34pon available", "High quality"),  # 3 -> e, 4 -> a
            ("c0c4ine", "Best price"),  # Multiple substitutions
            ("@dderall for sale", "Contact me"),  # @ -> a
        ]

        for title, description in test_cases:
            result = moderator.check_content(title=title, description=description)
            assert result.is_violation is True, f"Failed to detect leet speak: {title}"

    def test_evasion_spacing(self, moderator):
        """Test detection of basic spacing evasion in multi-word phrases."""
        # Note: Single-letter spacing (g u n s) is complex to detect without false positives
        # We focus on simpler patterns that are more reliably detectable
        test_cases = [
            ("fake  id  for  sale", "Good price"),  # Extra spaces
            ("replica    designer bag", "Contact me"),  # Multiple spaces
        ]

        for title, description in test_cases:
            result = moderator.check_content(title=title, description=description)
            assert result.is_violation is True, f"Failed to detect spacing: {title}"

    def test_evasion_separators(self, moderator):
        """Test detection of separator evasion (d_r_u_g_s, c-o-c-a-i-n-e)."""
        test_cases = [
            ("d_r_u_g_s", "Available now"),
            ("c-o-c-a-i-n-e", "Good price"),
            ("g.u.n for sale", "Contact me"),
        ]

        for title, description in test_cases:
            result = moderator.check_content(title=title, description=description)
            assert result.is_violation is True, f"Failed to detect separators: {title}"

    def test_external_url_detection(self, moderator):
        """Test detection of external marketplace URLs."""
        test_cases = [
            ("Great item", "See more at craigslist"),
            ("Buy now", "Also on facebook.com/marketplace"),
            ("Deals", "Check offerup for details"),
        ]

        for title, description in test_cases:
            result = moderator.check_content(title=title, description=description)
            assert result.is_violation is True, f"Failed to detect URL: {description}"

    def test_firearm_model_detection(self, moderator):
        """Test detection of popular firearm models."""
        test_cases = [
            ("Glock 19 for sale", "Great condition"),
            ("AR-15 available", "Contact me"),
            ("Smith Wesson", "Good price"),
        ]

        for title, description in test_cases:
            result = moderator.check_content(title=title, description=description)
            assert result.is_violation is True, f"Failed to detect firearm: {title}"
