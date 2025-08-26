"""Unit tests for keyword models."""

import pytest
from datetime import datetime
from models.keyword_models import (
    Keyword,
    NegativeKeyword,
    KeywordMetrics,
    KeywordCategory,
    KeywordExpansion,
    SeedKeyword,
    MatchType,
    KeywordStatus
)


class TestKeywordMetrics:
    """Test KeywordMetrics model."""
    
    def test_valid_metrics(self):
        """Test creating valid keyword metrics."""
        metrics = KeywordMetrics(
            search_volume=1000,
            cpc=2.50,
            competition=0.75,
            competition_level="high"
        )
        assert metrics.search_volume == 1000
        assert metrics.cpc == 2.50
        assert metrics.competition == 0.75
        assert metrics.competition_level == "high"
    
    def test_cpc_validation(self):
        """Test CPC validation and rounding."""
        metrics = KeywordMetrics(cpc=2.555)
        assert metrics.cpc == 2.56  # Should round to 2 decimal places
        
        with pytest.raises(ValueError):
            KeywordMetrics(cpc=-1.0)  # Negative CPC should fail
    
    def test_competition_bounds(self):
        """Test competition score bounds."""
        with pytest.raises(ValueError):
            KeywordMetrics(competition=1.5)  # Above 1.0 should fail
        
        with pytest.raises(ValueError):
            KeywordMetrics(competition=-0.1)  # Below 0 should fail
    
    def test_optional_fields(self):
        """Test that all fields are optional."""
        metrics = KeywordMetrics()
        assert metrics.search_volume is None
        assert metrics.cpc is None
        assert metrics.competition is None


class TestKeyword:
    """Test Keyword model."""
    
    def test_basic_keyword(self):
        """Test creating a basic keyword."""
        keyword = Keyword(term="plumber near me")
        assert keyword.term == "plumber near me"
        assert keyword.match_type == MatchType.BROAD
        assert keyword.status == KeywordStatus.PENDING
        assert keyword.language == "en"
    
    def test_term_normalization(self):
        """Test keyword term is cleaned and normalized."""
        keyword = Keyword(term="  Plumber Near Me  ")
        assert keyword.term == "plumber near me"
    
    def test_google_ads_format(self):
        """Test conversion to Google Ads format."""
        # Broad match
        keyword = Keyword(term="plumber", match_type=MatchType.BROAD)
        assert keyword.to_google_ads_format() == "plumber"
        
        # Phrase match
        keyword = Keyword(term="plumber near me", match_type=MatchType.PHRASE)
        assert keyword.to_google_ads_format() == '"plumber near me"'
        
        # Exact match
        keyword = Keyword(term="plumber", match_type=MatchType.EXACT)
        assert keyword.to_google_ads_format() == "[plumber]"
        
        # Broad match modifier
        keyword = Keyword(term="plumber near me", match_type=MatchType.BROAD_MODIFIER)
        assert keyword.to_google_ads_format() == "+plumber +near +me"
    
    def test_with_metrics(self):
        """Test keyword with metrics."""
        metrics = KeywordMetrics(search_volume=500, cpc=3.25)
        keyword = Keyword(
            term="emergency plumber",
            metrics=metrics,
            category="emergency services"
        )
        assert keyword.metrics.search_volume == 500
        assert keyword.metrics.cpc == 3.25
        assert keyword.category == "emergency services"
    
    def test_invalid_term(self):
        """Test that empty term fails validation."""
        with pytest.raises(ValueError):
            Keyword(term="")


class TestNegativeKeyword:
    """Test NegativeKeyword model."""
    
    def test_basic_negative_keyword(self):
        """Test creating a negative keyword."""
        neg_keyword = NegativeKeyword(
            term="free",
            reason="Low conversion intent"
        )
        assert neg_keyword.term == "free"
        assert neg_keyword.reason == "Low conversion intent"
        assert neg_keyword.match_type == MatchType.PHRASE
        assert neg_keyword.scope == "campaign"
        assert neg_keyword.auto_generated is False
    
    def test_term_normalization(self):
        """Test negative keyword term normalization."""
        neg_keyword = NegativeKeyword(
            term="  FREE  ",
            reason="test"
        )
        assert neg_keyword.term == "free"
    
    def test_confidence_bounds(self):
        """Test confidence score bounds."""
        neg_keyword = NegativeKeyword(
            term="test",
            reason="test",
            confidence=0.95
        )
        assert neg_keyword.confidence == 0.95
        
        with pytest.raises(ValueError):
            NegativeKeyword(term="test", reason="test", confidence=1.5)
        
        with pytest.raises(ValueError):
            NegativeKeyword(term="test", reason="test", confidence=-0.1)


class TestKeywordCategory:
    """Test KeywordCategory model."""
    
    def test_basic_category(self):
        """Test creating a keyword category."""
        category = KeywordCategory(
            name="Emergency Services",
            description="24/7 emergency plumbing services",
            keywords=["emergency plumber", "24 hour plumber"]
        )
        assert category.name == "Emergency Services"
        assert len(category.keywords) == 2
        assert category.priority == 0
    
    def test_hierarchical_categories(self):
        """Test categories with parent-child relationship."""
        category = KeywordCategory(
            name="Drain Cleaning",
            parent_category="Plumbing Services",
            priority=2
        )
        assert category.parent_category == "Plumbing Services"
        assert category.priority == 2
    
    def test_priority_bounds(self):
        """Test priority value bounds."""
        with pytest.raises(ValueError):
            KeywordCategory(name="Test", priority=11)  # Above 10
        
        with pytest.raises(ValueError):
            KeywordCategory(name="Test", priority=-1)  # Below 0


class TestKeywordExpansion:
    """Test KeywordExpansion model."""
    
    def test_basic_expansion(self):
        """Test creating a keyword expansion."""
        expansion = KeywordExpansion(
            seed_keyword="plumber",
            expanded_term="emergency plumber",
            expansion_type="related",
            relevance_score=0.85
        )
        assert expansion.seed_keyword == "plumber"
        assert expansion.expanded_term == "emergency plumber"
        assert expansion.relevance_score == 0.85
        assert expansion.approved is False
    
    def test_relevance_score_rounding(self):
        """Test relevance score is rounded."""
        expansion = KeywordExpansion(
            seed_keyword="test",
            expanded_term="test expanded",
            expansion_type="related",
            relevance_score=0.8567
        )
        assert expansion.relevance_score == 0.86
    
    def test_expansion_types(self):
        """Test valid expansion types."""
        valid_types = ["related", "similar", "long_tail", "question"]
        
        for exp_type in valid_types:
            expansion = KeywordExpansion(
                seed_keyword="test",
                expanded_term="test expanded",
                expansion_type=exp_type,
                relevance_score=0.5
            )
            assert expansion.expansion_type == exp_type
        
        # Invalid type
        with pytest.raises(ValueError):
            KeywordExpansion(
                seed_keyword="test",
                expanded_term="test",
                expansion_type="invalid",
                relevance_score=0.5
            )


class TestSeedKeyword:
    """Test SeedKeyword model."""
    
    def test_basic_seed_keyword(self):
        """Test creating a seed keyword."""
        seed = SeedKeyword(term="plumber")
        assert seed.term == "plumber"
        assert seed.priority == 1
        assert seed.expansion_limit == 50
        assert seed.include_questions is True
        assert seed.include_long_tail is True
    
    def test_term_cleaning(self):
        """Test seed keyword term cleaning."""
        seed = SeedKeyword(term="  Plumber  ")
        assert seed.term == "plumber"
    
    def test_expansion_settings(self):
        """Test expansion configuration."""
        seed = SeedKeyword(
            term="plumber",
            expansion_limit=100,
            include_questions=False,
            min_search_volume=50,
            max_cpc=5.00
        )
        assert seed.expansion_limit == 100
        assert seed.include_questions is False
        assert seed.min_search_volume == 50
        assert seed.max_cpc == 5.00
    
    def test_priority_bounds(self):
        """Test priority bounds."""
        with pytest.raises(ValueError):
            SeedKeyword(term="test", priority=0)  # Below 1
        
        with pytest.raises(ValueError):
            SeedKeyword(term="test", priority=6)  # Above 5
    
    def test_expansion_limit_bounds(self):
        """Test expansion limit bounds."""
        with pytest.raises(ValueError):
            SeedKeyword(term="test", expansion_limit=0)  # Below 1
        
        with pytest.raises(ValueError):
            SeedKeyword(term="test", expansion_limit=1001)  # Above 1000