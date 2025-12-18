import pytest
from app.services.diff_service import (
    extract_prices,
    extract_plan_names,
    has_free_tier,
    generate_diff,
    classify_change,
    CONFIDENCE_THRESHOLD
)
from app.models.change_event import ChangeType


class TestExtractPrices:
    def test_extract_usd_prices(self):
        text = "Our plans start at $10 per month and go up to $99.99"
        prices = extract_prices(text)
        assert len(prices) == 2
        assert "$10" in prices[0]
        assert "$99.99" in prices[1]
    
    def test_extract_euro_prices(self):
        text = "Price: €25.50 per user"
        prices = extract_prices(text)
        assert len(prices) == 1
        assert "€25.50" in prices[0]
    
    def test_extract_gbp_prices(self):
        text = "Starting from £15 monthly"
        prices = extract_prices(text)
        assert len(prices) == 1
        assert "£15" in prices[0]
    
    def test_extract_multiple_currencies(self):
        text = "$10 or €12 or £9"
        prices = extract_prices(text)
        assert len(prices) == 3
    
    def test_no_prices(self):
        text = "Contact us for pricing"
        prices = extract_prices(text)
        assert len(prices) == 0


class TestExtractPlanNames:
    def test_extract_plan_keywords(self):
        text = """
        Basic Plan - $10/mo
        Pro Tier - $25/mo
        Enterprise Package - Contact us
        """
        plans = extract_plan_names(text)
        assert len(plans) >= 2
        assert any("plan" in p for p in plans)
    
    def test_extract_subscription_levels(self):
        text = "Choose your subscription: Starter, Professional, Business"
        plans = extract_plan_names(text)
        assert len(plans) >= 1
        assert any("subscription" in p for p in plans)
    
    def test_no_plans(self):
        text = "Just some random text without pricing information"
        plans = extract_plan_names(text)
        assert len(plans) == 0


class TestHasFreeTier:
    def test_detect_free_keyword(self):
        text = "Try our Free plan today"
        assert has_free_tier(text) is True
    
    def test_detect_zero_price(self):
        text = "Starting at $0 per month"
        assert has_free_tier(text) is True
    
    def test_detect_trial(self):
        text = "14-day free trial available"
        assert has_free_tier(text) is True
    
    def test_no_free_tier(self):
        text = "Paid plans starting at $10"
        assert has_free_tier(text) is False


class TestGenerateDiff:
    def test_simple_addition(self):
        old = "Line 1\nLine 2"
        new = "Line 1\nLine 2\nLine 3"
        added, removed, changed = generate_diff(old, new)
        assert len(added) > 0
        assert len(removed) == 0
    
    def test_simple_removal(self):
        old = "Line 1\nLine 2\nLine 3"
        new = "Line 1\nLine 2"
        added, removed, changed = generate_diff(old, new)
        assert len(added) == 0
        assert len(removed) > 0
    
    def test_modification(self):
        old = "Price: $10"
        new = "Price: $15"
        added, removed, changed = generate_diff(old, new)
        assert len(added) > 0
        assert len(removed) > 0
    
    def test_no_change(self):
        text = "Same content"
        added, removed, changed = generate_diff(text, text)
        assert len(added) == 0
        assert len(removed) == 0


class TestClassifyChange:
    def test_price_increase(self):
        old_content = "Basic Plan: $10 per month"
        new_content = "Basic Plan: $20 per month"
        added, removed, changed = generate_diff(old_content, new_content)
        
        change_type, summary, confidence = classify_change(
            old_content, new_content, added, removed
        )
        
        assert change_type == ChangeType.price_increase
        assert confidence >= 0.7
        assert "increase" in summary.lower()
    
    def test_price_decrease(self):
        old_content = "Pro Plan: $50 per month"
        new_content = "Pro Plan: $30 per month"
        added, removed, changed = generate_diff(old_content, new_content)
        
        change_type, summary, confidence = classify_change(
            old_content, new_content, added, removed
        )
        
        assert change_type == ChangeType.price_decrease
        assert confidence >= 0.7
        assert "decrease" in summary.lower()
    
    def test_new_plan_added(self):
        old_content = "Basic Plan: $10\nPro Plan: $20"
        new_content = "Basic Plan: $10\nPro Plan: $20\nEnterprise Plan: $50"
        added, removed, changed = generate_diff(old_content, new_content)
        
        change_type, summary, confidence = classify_change(
            old_content, new_content, added, removed
        )
        
        assert change_type in [ChangeType.new_plan_added, ChangeType.price_increase]
        assert confidence >= 0.6
    
    def test_plan_removed(self):
        old_content = "Basic Plan: $10\nPro Plan: $20\nEnterprise Plan: $50"
        new_content = "Basic Plan: $10\nPro Plan: $20"
        added, removed, changed = generate_diff(old_content, new_content)
        
        change_type, summary, confidence = classify_change(
            old_content, new_content, added, removed
        )
        
        assert change_type in [ChangeType.plan_removed, ChangeType.unknown]
        assert confidence >= 0.5
    
    def test_free_tier_removed(self):
        old_content = "Free Plan: $0 forever\nPro Plan: $20"
        new_content = "Pro Plan: $20\nEnterprise Plan: $50"
        added, removed, changed = generate_diff(old_content, new_content)
        
        change_type, summary, confidence = classify_change(
            old_content, new_content, added, removed
        )
        
        assert change_type == ChangeType.free_tier_removed
        assert confidence >= 0.8
        assert "free tier" in summary.lower()
    
    def test_minor_change_low_confidence(self):
        old_content = "Updated: January 1, 2024"
        new_content = "Updated: January 2, 2024"
        added, removed, changed = generate_diff(old_content, new_content)
        
        change_type, summary, confidence = classify_change(
            old_content, new_content, added, removed
        )
        
        assert confidence < CONFIDENCE_THRESHOLD
    
    def test_unknown_change_type(self):
        old_content = "Some random text here"
        new_content = "Some different text here"
        added, removed, changed = generate_diff(old_content, new_content)
        
        change_type, summary, confidence = classify_change(
            old_content, new_content, added, removed
        )
        
        assert change_type == ChangeType.unknown
    
    def test_multiple_price_changes(self):
        old_content = "Basic: $10, Pro: $20, Enterprise: $50"
        new_content = "Basic: $15, Pro: $30, Enterprise: $75"
        added, removed, changed = generate_diff(old_content, new_content)
        
        change_type, summary, confidence = classify_change(
            old_content, new_content, added, removed
        )
        
        assert change_type == ChangeType.price_increase
        assert confidence >= 0.7


class TestConfidenceScoring:
    def test_high_confidence_price_change(self):
        old_content = "Monthly: $10"
        new_content = "Monthly: $20"
        added, removed, changed = generate_diff(old_content, new_content)
        
        _, _, confidence = classify_change(old_content, new_content, added, removed)
        
        assert confidence >= 0.8
    
    def test_medium_confidence_plan_change(self):
        old_content = "Basic Plan\nPro Plan"
        new_content = "Basic Plan\nPro Plan\nEnterprise Plan"
        added, removed, changed = generate_diff(old_content, new_content)
        
        _, _, confidence = classify_change(old_content, new_content, added, removed)
        
        assert 0.5 <= confidence < 0.9
    
    def test_low_confidence_minor_change(self):
        old_content = "Last updated: Today"
        new_content = "Last updated: Yesterday"
        added, removed, changed = generate_diff(old_content, new_content)
        
        _, _, confidence = classify_change(old_content, new_content, added, removed)
        
        assert confidence <= 0.6


class TestEdgeCases:
    def test_empty_content(self):
        old_content = ""
        new_content = "New content"
        added, removed, changed = generate_diff(old_content, new_content)
        
        change_type, summary, confidence = classify_change(
            old_content, new_content, added, removed
        )
        
        assert change_type == ChangeType.unknown
    
    def test_identical_content(self):
        content = "Same content"
        added, removed, changed = generate_diff(content, content)
        
        change_type, summary, confidence = classify_change(
            content, content, added, removed
        )
        
        assert confidence < CONFIDENCE_THRESHOLD
    
    def test_price_with_whitespace(self):
        text = "Price: $ 10 . 50"
        prices = extract_prices(text)
        assert len(prices) >= 1
    
    def test_case_insensitive_free_tier(self):
        assert has_free_tier("FREE PLAN") is True
        assert has_free_tier("Free plan") is True
        assert has_free_tier("free") is True

