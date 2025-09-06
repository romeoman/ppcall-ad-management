"""
Ad Group Organization Module

This module provides functionality to organize keywords into logical ad groups
based on services, categories, and locations. It handles different match types
and formats the output for Google Ads and Bing Ads import.
"""

from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass
import logging
from collections import defaultdict
import re

from models.keyword_models import Keyword, KeywordMetrics, MatchType
from models.ad_group_models import AdGroup, AdGroupKeyword

logger = logging.getLogger(__name__)


class AdGroupProcessor:
    """
    Processes keywords into organized ad groups for PPC campaigns.
    
    This processor handles:
    - Grouping keywords by category and location
    - Creating ad groups with different match types
    - Balancing ad group sizes
    - Formatting for platform-specific import
    - Suggesting bid adjustments based on competition
    """
    
    # Constants for ad group optimization
    MIN_KEYWORDS_PER_GROUP = 3
    MAX_KEYWORDS_PER_GROUP = 50
    OPTIMAL_KEYWORDS_PER_GROUP = 15
    
    # Available match types
    MATCH_TYPES = ['broad', 'phrase', 'exact']
    
    def __init__(self, 
                 min_keywords: int = None,
                 max_keywords: int = None,
                 optimal_keywords: int = None):
        """
        Initialize the AdGroupProcessor.
        
        Args:
            min_keywords: Minimum keywords per ad group (default: 3)
            max_keywords: Maximum keywords per ad group (default: 50)
            optimal_keywords: Optimal keywords per ad group (default: 15)
        """
        self.min_keywords = min_keywords or self.MIN_KEYWORDS_PER_GROUP
        self.max_keywords = max_keywords or self.MAX_KEYWORDS_PER_GROUP
        self.optimal_keywords = optimal_keywords or self.OPTIMAL_KEYWORDS_PER_GROUP
        
        logger.info(f"AdGroupProcessor initialized with limits: "
                   f"min={self.min_keywords}, max={self.max_keywords}, "
                   f"optimal={self.optimal_keywords}")
    
    def create_ad_groups(self, 
                        keywords: List[Keyword],
                        match_types: Optional[List[str]] = None,
                        group_by_intent: bool = True,
                        balance_groups: bool = True) -> List[AdGroup]:
        """
        Create ad groups from a list of keywords.
        
        Args:
            keywords: List of Keyword objects to organize
            match_types: List of match types to create (default: ['broad'])
            group_by_intent: Whether to group by search intent
            balance_groups: Whether to balance group sizes
            
        Returns:
            List of AdGroup objects
            
        Raises:
            ValueError: If invalid match types are provided
        """
        if not keywords:
            logger.warning("No keywords provided to create ad groups")
            return []
        
        # Default to broad match if not specified
        if not match_types:
            match_types = ['broad']
        
        # Validate match types
        for match_type in match_types:
            if match_type not in self.MATCH_TYPES:
                raise ValueError(f"Invalid match type: {match_type}. "
                               f"Must be one of {self.MATCH_TYPES}")
        
        logger.info(f"Creating ad groups for {len(keywords)} keywords "
                   f"with match types: {match_types}")
        
        # Group keywords
        keyword_groups = self._group_keywords(keywords, group_by_intent)
        
        # Balance groups if requested
        if balance_groups:
            keyword_groups = self._balance_groups(keyword_groups)
        
        # Create ad groups for each keyword group and match type
        ad_groups = []
        for group_key, group_keywords in keyword_groups.items():
            for match_type in match_types:
                ad_group = self._create_single_ad_group(
                    group_key, 
                    group_keywords, 
                    match_type
                )
                ad_groups.append(ad_group)
        
        logger.info(f"Created {len(ad_groups)} ad groups")
        return ad_groups
    
    def _group_keywords(self, 
                       keywords: List[Keyword],
                       group_by_intent: bool) -> Dict[str, List[Keyword]]:
        """
        Group keywords by category, location, and optionally intent.
        
        Args:
            keywords: List of keywords to group
            group_by_intent: Whether to group by search intent
            
        Returns:
            Dictionary mapping group keys to lists of keywords
        """
        groups = defaultdict(list)
        
        for keyword in keywords:
            # Create group key based on attributes
            key_parts = []
            
            # Always group by category
            if keyword.category:
                key_parts.append(keyword.category)
            
            # Always group by location if present
            if keyword.location:
                key_parts.append(keyword.location)
            
            # Optionally group by intent from metadata
            if group_by_intent and keyword.metadata:
                intent = keyword.metadata.get('search_intent')
                if intent:
                    key_parts.append(intent)
            
            # Default key if no attributes
            if not key_parts:
                key_parts.append("General")
            
            group_key = " - ".join(key_parts)
            groups[group_key].append(keyword)
        
        logger.debug(f"Created {len(groups)} keyword groups")
        return dict(groups)
    
    def _balance_groups(self, 
                       groups: Dict[str, List[Keyword]]) -> Dict[str, List[Keyword]]:
        """
        Balance ad groups to optimal sizes by splitting or merging.
        
        Args:
            groups: Dictionary of keyword groups
            
        Returns:
            Balanced dictionary of keyword groups
        """
        balanced_groups = {}
        
        for group_key, keywords in groups.items():
            group_size = len(keywords)
            
            # Group is within acceptable range
            if self.min_keywords <= group_size <= self.max_keywords:
                balanced_groups[group_key] = keywords
            
            # Group is too large - split it
            elif group_size > self.max_keywords:
                split_groups = self._split_large_group(group_key, keywords)
                balanced_groups.update(split_groups)
            
            # Group is too small - mark for merging
            else:
                # For now, keep small groups but log a warning
                logger.warning(f"Ad group '{group_key}' has only {group_size} keywords "
                             f"(minimum recommended: {self.min_keywords})")
                balanced_groups[group_key] = keywords
        
        # Merge very small groups if possible
        balanced_groups = self._merge_small_groups(balanced_groups)
        
        return balanced_groups
    
    def _split_large_group(self, 
                          group_key: str,
                          keywords: List[Keyword]) -> Dict[str, List[Keyword]]:
        """
        Split a large group into smaller, optimally-sized groups.
        
        Args:
            group_key: Original group key
            keywords: List of keywords in the group
            
        Returns:
            Dictionary of split groups
        """
        split_groups = {}
        
        # Calculate number of splits needed
        num_splits = (len(keywords) + self.optimal_keywords - 1) // self.optimal_keywords
        
        # Sort keywords by search volume for even distribution
        sorted_keywords = sorted(keywords, 
                                key=lambda k: k.metrics.search_volume if k.metrics else 0, 
                                reverse=True)
        
        # Distribute keywords evenly across splits
        for i in range(num_splits):
            split_key = f"{group_key} #{i+1}"
            start_idx = i * self.optimal_keywords
            end_idx = min((i + 1) * self.optimal_keywords, len(sorted_keywords))
            split_groups[split_key] = sorted_keywords[start_idx:end_idx]
            
            logger.debug(f"Split group '{group_key}' -> '{split_key}' "
                        f"with {len(split_groups[split_key])} keywords")
        
        return split_groups
    
    def _merge_small_groups(self, 
                           groups: Dict[str, List[Keyword]]) -> Dict[str, List[Keyword]]:
        """
        Merge very small groups with similar groups.
        
        Args:
            groups: Dictionary of keyword groups
            
        Returns:
            Dictionary with merged groups
        """
        merged_groups = {}
        small_groups = []
        
        # Identify small groups
        for group_key, keywords in groups.items():
            if len(keywords) < self.min_keywords:
                small_groups.append((group_key, keywords))
            else:
                merged_groups[group_key] = keywords
        
        # Try to merge small groups
        if small_groups:
            # Group small groups by similarity (simplified: by first word)
            merge_candidates = defaultdict(list)
            for key, keywords in small_groups:
                first_word = key.split()[0] if key else "Other"
                merge_candidates[first_word].extend(keywords)
            
            # Create merged groups
            for merge_key, merged_keywords in merge_candidates.items():
                if len(merged_keywords) >= self.min_keywords:
                    merged_key = f"{merge_key} - Merged"
                    merged_groups[merged_key] = merged_keywords
                    logger.info(f"Merged small groups into '{merged_key}' "
                              f"with {len(merged_keywords)} keywords")
                else:
                    # Still too small, add to a general group
                    if "General - Small Groups" not in merged_groups:
                        merged_groups["General - Small Groups"] = []
                    merged_groups["General - Small Groups"].extend(merged_keywords)
        
        return merged_groups
    
    def _create_single_ad_group(self,
                               group_key: str,
                               keywords: List[Keyword],
                               match_type: str) -> AdGroup:
        """
        Create a single ad group from keywords.
        
        Args:
            group_key: Key identifying the group
            keywords: List of keywords for the group
            match_type: Match type for the ad group
            
        Returns:
            AdGroup object
        """
        # Create ad group name
        ad_group_name = f"{group_key} - {match_type.capitalize()}"
        
        # Convert keywords to AdGroupKeyword objects
        ad_group_keywords = []
        for keyword in keywords:
            # Create a new Keyword object with the appropriate match type
            keyword_obj = Keyword(
                term=keyword.term,
                match_type=MatchType(match_type),
                metrics=keyword.metrics,
                category=keyword.category,
                location=keyword.location,
                language=keyword.language,
                status=keyword.status,
                source=keyword.source,
                metadata=keyword.metadata
            )
            
            ad_group_keyword = AdGroupKeyword(
                keyword=keyword_obj,
                bid=self._suggest_bid(keyword),
                final_url=None  # To be set later if needed
            )
            ad_group_keywords.append(ad_group_keyword)
        
        # Calculate aggregate metrics for the ad group
        total_search_volume = sum(
            k.metrics.search_volume if k.metrics and k.metrics.search_volume else 0 
            for k in keywords
        )
        avg_competition = sum(
            k.metrics.competition if k.metrics and k.metrics.competition else 0.5 
            for k in keywords
        ) / len(keywords) if keywords else 0.5
        avg_cpc = sum(
            k.metrics.cpc if k.metrics and k.metrics.cpc else 0 
            for k in keywords
        ) / len(keywords) if keywords else 0
        
        # Create the ad group
        ad_group = AdGroup(
            name=ad_group_name,
            campaign_name="Campaign",  # Default campaign name
            keywords=ad_group_keywords,
            default_bid=self._calculate_default_bid(avg_cpc, avg_competition),
            status='enabled'
        )
        
        # Store metadata for reporting
        ad_group.metadata = {
            'total_search_volume': total_search_volume,
            'avg_competition': avg_competition,
            'avg_cpc': avg_cpc,
            'keyword_count': len(ad_group_keywords)
        }
        
        logger.debug(f"Created ad group '{ad_group_name}' with {len(ad_group_keywords)} keywords")
        return ad_group
    
    def _format_keyword_for_match_type(self, keyword: str, match_type: str) -> str:
        """
        Format a keyword string based on match type.
        
        Args:
            keyword: Raw keyword string
            match_type: Match type (broad, phrase, exact)
            
        Returns:
            Formatted keyword string
        """
        # Clean the keyword first
        keyword = keyword.strip()
        
        if match_type == 'broad':
            # Broad match - no special formatting
            return keyword
        elif match_type == 'phrase':
            # Phrase match - wrap in quotes
            return f'"{keyword}"'
        elif match_type == 'exact':
            # Exact match - wrap in brackets
            return f'[{keyword}]'
        else:
            return keyword
    
    def _suggest_bid(self, keyword: Keyword) -> Optional[float]:
        """
        Suggest a bid for a keyword based on competition and CPC data.
        
        Args:
            keyword: Keyword object with metrics
            
        Returns:
            Suggested bid amount or None
        """
        # Get CPC if available from metrics
        if not keyword.metrics or not keyword.metrics.cpc:
            return None
        
        cpc = keyword.metrics.cpc
        
        # Get competition level
        competition = keyword.metrics.competition if keyword.metrics else 0.5
        
        # Adjust bid based on competition
        # High competition: bid slightly above CPC
        # Low competition: bid at or below CPC
        if competition > 0.7:
            suggested_bid = cpc * 1.2
        elif competition > 0.4:
            suggested_bid = cpc * 1.0
        else:
            suggested_bid = cpc * 0.8
        
        # Round to 2 decimal places
        return round(suggested_bid, 2)
    
    def _calculate_default_bid(self, avg_cpc: float, avg_competition: float) -> float:
        """
        Calculate a default bid for an ad group.
        
        Args:
            avg_cpc: Average CPC of keywords in the group
            avg_competition: Average competition level
            
        Returns:
            Default bid amount
        """
        if avg_cpc == 0:
            # No CPC data, use a conservative default
            return 1.00
        
        # Similar logic to individual keyword bids
        if avg_competition > 0.7:
            default_bid = avg_cpc * 1.15
        elif avg_competition > 0.4:
            default_bid = avg_cpc * 1.0
        else:
            default_bid = avg_cpc * 0.85
        
        # Round to 2 decimal places
        return round(default_bid, 2)
    
    def format_for_google_ads(self, ad_groups: List[AdGroup]) -> List[Dict[str, Any]]:
        """
        Format ad groups for Google Ads import.
        
        Args:
            ad_groups: List of AdGroup objects
            
        Returns:
            List of dictionaries formatted for Google Ads CSV export
        """
        formatted_data = []
        
        for ad_group in ad_groups:
            campaign_name = ad_group.campaign_name or "Campaign"
            
            # Add ad group row
            formatted_data.append({
                'Campaign': campaign_name,
                'Ad Group': ad_group.name,
                'Max CPC': ad_group.default_bid,
                'Ad Group Type': 'Standard',
                'Ad Group Status': ad_group.status.capitalize()
            })
            
            # Add keyword rows
            for ad_keyword in ad_group.keywords:
                # Format keyword based on match type
                formatted_keyword = ad_keyword.keyword.to_google_ads_format()
                
                formatted_data.append({
                    'Campaign': campaign_name,
                    'Ad Group': ad_group.name,
                    'Keyword': formatted_keyword,
                    'Criterion Type': 'Keyword',
                    'Match Type': ad_keyword.keyword.match_type.capitalize() if hasattr(ad_keyword.keyword.match_type, 'capitalize') else str(ad_keyword.keyword.match_type).capitalize(),
                    'Max CPC': ad_keyword.bid or ad_group.default_bid,
                    'Keyword Status': 'Enabled'
                })
        
        logger.info(f"Formatted {len(ad_groups)} ad groups for Google Ads export")
        return formatted_data
    
    def format_for_bing_ads(self, ad_groups: List[AdGroup]) -> List[Dict[str, Any]]:
        """
        Format ad groups for Bing Ads import.
        
        Args:
            ad_groups: List of AdGroup objects
            
        Returns:
            List of dictionaries formatted for Bing Ads CSV export
        """
        formatted_data = []
        
        for ad_group in ad_groups:
            campaign_name = ad_group.campaign_name or "Campaign"
            
            # Bing Ads uses slightly different column names
            for ad_keyword in ad_group.keywords:
                # Format keyword based on match type
                formatted_keyword = ad_keyword.keyword.to_google_ads_format()
                
                formatted_data.append({
                    'Campaign': campaign_name,
                    'Ad Group': ad_group.name,
                    'Keyword': formatted_keyword,
                    'Match Type': ad_keyword.keyword.match_type.capitalize() if hasattr(ad_keyword.keyword.match_type, 'capitalize') else str(ad_keyword.keyword.match_type).capitalize(),
                    'Bid': ad_keyword.bid or ad_group.default_bid,
                    'Status': 'Active'
                })
        
        logger.info(f"Formatted {len(ad_groups)} ad groups for Bing Ads export")
        return formatted_data
    
    def get_ad_group_statistics(self, ad_groups: List[AdGroup]) -> Dict[str, Any]:
        """
        Calculate statistics for a list of ad groups.
        
        Args:
            ad_groups: List of AdGroup objects
            
        Returns:
            Dictionary containing statistics
        """
        if not ad_groups:
            return {
                'total_ad_groups': 0,
                'total_keywords': 0,
                'avg_keywords_per_group': 0,
                'match_type_distribution': {},
                'bid_range': {'min': 0, 'max': 0, 'avg': 0}
            }
        
        # Calculate statistics
        total_keywords = sum(len(ag.keywords) for ag in ad_groups)
        avg_keywords = total_keywords / len(ad_groups)
        
        # Match type distribution
        match_types = defaultdict(int)
        all_bids = []
        
        for ad_group in ad_groups:
            for ad_keyword in ad_group.keywords:
                match_types[ad_keyword.keyword.match_type] += 1
                if ad_keyword.bid:
                    all_bids.append(ad_keyword.bid)
        
        # Bid statistics
        bid_stats = {
            'min': min(all_bids) if all_bids else 0,
            'max': max(all_bids) if all_bids else 0,
            'avg': sum(all_bids) / len(all_bids) if all_bids else 0
        }
        
        return {
            'total_ad_groups': len(ad_groups),
            'total_keywords': total_keywords,
            'avg_keywords_per_group': round(avg_keywords, 1),
            'match_type_distribution': dict(match_types),
            'bid_range': bid_stats,
            'groups_by_size': self._categorize_by_size(ad_groups)
        }
    
    def _categorize_by_size(self, ad_groups: List[AdGroup]) -> Dict[str, int]:
        """
        Categorize ad groups by size.
        
        Args:
            ad_groups: List of AdGroup objects
            
        Returns:
            Dictionary with size categories and counts
        """
        categories = {
            'small': 0,  # < min_keywords
            'optimal': 0,  # min_keywords to optimal_keywords
            'large': 0,  # optimal_keywords to max_keywords
            'oversized': 0  # > max_keywords
        }
        
        for ad_group in ad_groups:
            size = len(ad_group.keywords)
            if size < self.min_keywords:
                categories['small'] += 1
            elif size <= self.optimal_keywords:
                categories['optimal'] += 1
            elif size <= self.max_keywords:
                categories['large'] += 1
            else:
                categories['oversized'] += 1
        
        return categories
    
    def validate_ad_groups(self, ad_groups: List[AdGroup]) -> List[str]:
        """
        Validate ad groups for common issues.
        
        Args:
            ad_groups: List of AdGroup objects
            
        Returns:
            List of validation warnings/errors
        """
        issues = []
        
        # Check for duplicate ad group names
        names = [ag.name for ag in ad_groups]
        duplicates = [name for name in names if names.count(name) > 1]
        if duplicates:
            issues.append(f"Duplicate ad group names found: {set(duplicates)}")
        
        # Check individual ad groups
        for ad_group in ad_groups:
            # Check size
            size = len(ad_group.keywords)
            if size < self.min_keywords:
                issues.append(f"Ad group '{ad_group.name}' has only {size} keywords "
                            f"(minimum recommended: {self.min_keywords})")
            elif size > self.max_keywords:
                issues.append(f"Ad group '{ad_group.name}' has {size} keywords "
                            f"(maximum recommended: {self.max_keywords})")
            
            # Check for duplicate keywords within ad group
            keywords = [kw.keyword.term for kw in ad_group.keywords]
            kw_duplicates = [kw for kw in keywords if keywords.count(kw) > 1]
            if kw_duplicates:
                issues.append(f"Ad group '{ad_group.name}' has duplicate keywords: "
                            f"{set(kw_duplicates)}")
            
            # Check for missing bids
            missing_bids = [kw.keyword.term for kw in ad_group.keywords if not kw.bid]
            if missing_bids and not ad_group.default_bid:
                issues.append(f"Ad group '{ad_group.name}' has keywords without bids "
                            f"and no default bid set")
        
        return issues