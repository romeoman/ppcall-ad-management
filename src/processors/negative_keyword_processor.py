"""
Negative Keyword Processor Module

Handles automatic generation and processing of negative keywords for PPC campaigns.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import logging
from pathlib import Path
import json
from datetime import datetime

from models.keyword_models import NegativeKeyword, Keyword, ExpandedKeyword, MatchType

# Configure logging
logger = logging.getLogger(__name__)


class NegativeKeywordProcessor:
    """
    Processes negative keywords including automatic generation, categorization, 
    and conflict detection.
    """
    
    def __init__(self, custom_negatives_path: Optional[Path] = None):
        """
        Initialize NegativeKeywordProcessor with default and custom negative keyword lists.
        
        Args:
            custom_negatives_path: Optional path to custom negative keywords JSON file
        """
        # Default negative keywords by category
        self.default_negatives = self._get_default_negatives()
        
        # Load custom negatives if provided
        self.custom_negatives = {}
        if custom_negatives_path and custom_negatives_path.exists():
            try:
                with open(custom_negatives_path, 'r') as f:
                    self.custom_negatives = json.load(f)
                logger.info(f"Loaded custom negatives from {custom_negatives_path}")
            except Exception as e:
                logger.error(f"Error loading custom negatives: {e}")
        
        logger.info("NegativeKeywordProcessor initialized")
    
    def _get_default_negatives(self) -> Dict[str, List[Dict[str, str]]]:
        """Get comprehensive default negative keywords for home services."""
        return {
            'general': [
                # No monetization potential
                {'term': 'free', 'reason': 'No monetization potential'},
                {'term': 'diy', 'reason': 'Do-it-yourself searches'},
                {'term': 'how to', 'reason': 'Informational/DIY intent'},
                {'term': 'yourself', 'reason': 'DIY intent'},
                
                # Low-value customers
                {'term': 'cheap', 'reason': 'Low-value customers'},
                {'term': 'cheapest', 'reason': 'Price-only shoppers'},
                {'term': 'discount', 'reason': 'Bargain hunters'},
                
                # Job seekers
                {'term': 'jobs', 'reason': 'Job seekers, not customers'},
                {'term': 'careers', 'reason': 'Job seekers'},
                {'term': 'hiring', 'reason': 'Job seekers'},
                {'term': 'employment', 'reason': 'Job seekers'},
                {'term': 'salary', 'reason': 'Job information seekers'},
                {'term': 'wages', 'reason': 'Job information seekers'},
                
                # Educational/Informational
                {'term': 'training', 'reason': 'Educational content seekers'},
                {'term': 'course', 'reason': 'Educational content'},
                {'term': 'tutorial', 'reason': 'Educational content'},
                {'term': 'guide', 'reason': 'Informational content'},
                {'term': 'manual', 'reason': 'Product manual seekers'},
                {'term': 'instructions', 'reason': 'DIY/Informational'},
                
                # Media content seekers
                {'term': 'youtube', 'reason': 'Video content seekers'},
                {'term': 'video', 'reason': 'Video content seekers'},
                {'term': 'watch', 'reason': 'Video content seekers'},
                
                # Reviews/Research
                {'term': 'review', 'reason': 'Research phase, not ready to buy'},
                {'term': 'reviews', 'reason': 'Research phase'},
                {'term': 'complaints', 'reason': 'Negative research'},
                {'term': 'scam', 'reason': 'Trust issues'},
                
                # Parts/Supplies (for service businesses)
                {'term': 'parts', 'reason': 'Parts shoppers, not service seekers'},
                {'term': 'supplies', 'reason': 'Supply shoppers'},
                {'term': 'tools', 'reason': 'Tool shoppers, not service seekers'},
                {'term': 'equipment rental', 'reason': 'Equipment renters, not service seekers'}
            ],
            
            'emergency_plumbing': [
                {'term': 'school', 'reason': 'Educational searches'},
                {'term': 'apprentice', 'reason': 'Job/training searches'},
                {'term': 'license', 'reason': 'Professional licensing info'},
                {'term': 'certification', 'reason': 'Professional certification'},
                {'term': 'become a plumber', 'reason': 'Career information'},
                {'term': 'plumbing code', 'reason': 'Regulatory information'},
                {'term': 'wholesale', 'reason': 'B2B/wholesale searches'},
                {'term': 'diagram', 'reason': 'Technical information seekers'},
                {'term': 'blueprint', 'reason': 'Technical drawings'},
                {'term': 'history', 'reason': 'Educational/historical content'}
            ],
            
            'water_cleanup': [
                {'term': 'insurance claim', 'reason': 'Insurance process info'},
                {'term': 'insurance cover', 'reason': 'Coverage questions'},
                {'term': 'fema', 'reason': 'Government assistance'},
                {'term': 'flood zone', 'reason': 'Zoning information'},
                {'term': 'prevention', 'reason': 'Preventive info, not service'},
                {'term': 'causes', 'reason': 'Informational searches'},
                {'term': 'statistics', 'reason': 'Research/data seekers'},
                {'term': 'news', 'reason': 'News/current events'},
                {'term': 'before and after', 'reason': 'Portfolio viewers'}
            ],
            
            'toilet_repairs': [
                {'term': 'replacement parts', 'reason': 'Parts shoppers'},
                {'term': 'home depot', 'reason': 'Retail shoppers'},
                {'term': 'lowes', 'reason': 'Retail shoppers'},
                {'term': 'amazon', 'reason': 'Online shoppers'},
                {'term': 'ebay', 'reason': 'Online marketplace'},
                {'term': 'install', 'reason': 'DIY installation'},
                {'term': 'installation guide', 'reason': 'DIY guides'},
                {'term': 'warranty', 'reason': 'Warranty information'},
                {'term': 'recall', 'reason': 'Product recall info'},
                {'term': 'model number', 'reason': 'Parts/specs searches'}
            ],
            
            'leak_detection': [
                {'term': 'detector', 'reason': 'Device shoppers, not service'},
                {'term': 'sensor', 'reason': 'Device shoppers'},
                {'term': 'alarm', 'reason': 'Device shoppers'},
                {'term': 'monitor', 'reason': 'Device shoppers'},
                {'term': 'smart home', 'reason': 'IoT device searches'},
                {'term': 'app', 'reason': 'Software searches'},
                {'term': 'meter reading', 'reason': 'Utility information'},
                {'term': 'water bill', 'reason': 'Billing questions'},
                {'term': 'calculate', 'reason': 'Calculator/tool searches'}
            ],
            
            'pipe_repair': [
                {'term': 'copper vs pvc', 'reason': 'Comparison research'},
                {'term': 'pex', 'reason': 'Material research'},
                {'term': 'threading', 'reason': 'Technical specifications'},
                {'term': 'fittings', 'reason': 'Parts searches'},
                {'term': 'solder', 'reason': 'DIY supplies'},
                {'term': 'tape', 'reason': 'DIY supplies'},
                {'term': 'putty', 'reason': 'DIY supplies'},
                {'term': 'temporary fix', 'reason': 'DIY temporary solutions'},
                {'term': 'hack', 'reason': 'DIY workarounds'}
            ],
            
            'sewer_line': [
                {'term': 'septic', 'reason': 'Different service type'},
                {'term': 'city', 'reason': 'Municipal information'},
                {'term': 'public works', 'reason': 'Government services'},
                {'term': 'easement', 'reason': 'Legal/property info'},
                {'term': 'permit', 'reason': 'Regulatory information'},
                {'term': 'inspection', 'reason': 'Official inspections'},
                {'term': 'camera rental', 'reason': 'Equipment rental'},
                {'term': 'locate', 'reason': 'Utility marking services'}
            ],
            
            'water_heater': [
                {'term': 'tankless vs tank', 'reason': 'Comparison research'},
                {'term': 'energy star', 'reason': 'Product research'},
                {'term': 'rebate', 'reason': 'Financial incentives'},
                {'term': 'tax credit', 'reason': 'Financial incentives'},
                {'term': 'pilot light', 'reason': 'DIY troubleshooting'},
                {'term': 'reset button', 'reason': 'DIY troubleshooting'},
                {'term': 'thermocouple', 'reason': 'Parts searches'},
                {'term': 'element', 'reason': 'Parts searches'},
                {'term': 'anode rod', 'reason': 'Parts searches'},
                {'term': 'flush', 'reason': 'DIY maintenance'}
            ],
            
            'drain_cleaning': [
                {'term': 'snake rental', 'reason': 'Equipment rental'},
                {'term': 'chemical', 'reason': 'DIY chemical solutions'},
                {'term': 'drano', 'reason': 'DIY products'},
                {'term': 'liquid plumber', 'reason': 'DIY products'},
                {'term': 'baking soda', 'reason': 'DIY home remedies'},
                {'term': 'vinegar', 'reason': 'DIY home remedies'},
                {'term': 'plunger', 'reason': 'DIY tools'},
                {'term': 'hair clog', 'reason': 'DIY-level problems'},
                {'term': 'prevention tips', 'reason': 'Informational content'}
            ]
        }
    
    def generate_negative_keywords(
        self,
        categories: List[str],
        custom_negatives: Optional[List[Dict[str, str]]] = None,
        include_general: bool = True
    ) -> List[NegativeKeyword]:
        """
        Generate negative keywords based on categories and custom inputs.
        
        Args:
            categories: List of category names to get negatives for
            custom_negatives: Optional list of custom negative keywords
            include_general: Whether to include general negative keywords
        
        Returns:
            List of NegativeKeyword objects
        """
        negatives = []
        processed_terms = set()
        
        # Add general negatives if requested
        if include_general and 'general' in self.default_negatives:
            for neg in self.default_negatives['general']:
                if neg['term'].lower() not in processed_terms:
                    negatives.append(NegativeKeyword(
                        term=neg['term'],
                        reason=neg['reason'],
                        auto_generated=True
                    ))
                    processed_terms.add(neg['term'].lower())
        
        # Add category-specific negatives
        for category in categories:
            category_lower = category.lower().replace(' ', '_')
            
            # Check default negatives
            if category_lower in self.default_negatives:
                for neg in self.default_negatives[category_lower]:
                    if neg['term'].lower() not in processed_terms:
                        negatives.append(NegativeKeyword(
                            term=neg['term'],
                            reason=neg['reason'],
                            auto_generated=True
                        ))
                        processed_terms.add(neg['term'].lower())
            
            # Check custom negatives
            if category_lower in self.custom_negatives:
                for neg in self.custom_negatives[category_lower]:
                    if neg['term'].lower() not in processed_terms:
                        negatives.append(NegativeKeyword(
                            term=neg['term'],
                            reason=neg.get('reason', 'Custom negative keyword'),
                            auto_generated=False
                        ))
                        processed_terms.add(neg['term'].lower())
        
        # Add user-provided custom negatives
        if custom_negatives:
            for neg in custom_negatives:
                if neg is None:  # Skip None values
                    continue
                term = neg.get('term', neg) if isinstance(neg, dict) else str(neg)
                if term and term.lower() not in processed_terms:  # Check term is not empty
                    negatives.append(NegativeKeyword(
                        term=term,
                        reason=neg.get('reason', 'User-provided negative') if isinstance(neg, dict) else 'User-provided negative',
                        auto_generated=False
                    ))
                    processed_terms.add(term.lower())
        
        logger.info(f"Generated {len(negatives)} negative keywords for categories: {categories}")
        return negatives
    
    def check_keyword_conflicts(
        self,
        keywords: List[Any],  # Can be Keyword, ExpandedKeyword, or dict
        negative_keywords: List[NegativeKeyword]
    ) -> List[Dict[str, Any]]:
        """
        Check for conflicts between keywords and negative keywords.
        
        Args:
            keywords: List of keyword objects or dictionaries
            negative_keywords: List of negative keywords
        
        Returns:
            List of conflict dictionaries with details and resolutions
        """
        conflicts = []
        
        # Create set of negative terms for faster lookup
        neg_terms = {neg.term.lower() for neg in negative_keywords}
        
        for keyword in keywords:
            # Extract keyword term based on object type
            if isinstance(keyword, dict):
                kw_term = keyword.get('keyword', keyword.get('term', ''))
            elif hasattr(keyword, 'keyword'):
                kw_term = keyword.keyword
            elif hasattr(keyword, 'term'):
                kw_term = keyword.term
            else:
                kw_term = str(keyword)
            
            if not kw_term:
                continue
            
            kw_lower = kw_term.lower()
            
            # Check for exact and partial matches
            for neg_term in neg_terms:
                conflict_type = None
                
                # Exact match
                if neg_term == kw_lower:
                    conflict_type = 'exact'
                # Negative term is contained in keyword
                elif neg_term in kw_lower.split():
                    conflict_type = 'word_match'
                # Partial match (substring)
                elif neg_term in kw_lower:
                    conflict_type = 'partial'
                
                if conflict_type:
                    conflicts.append({
                        'keyword': kw_term,
                        'negative': neg_term,
                        'conflict_type': conflict_type,
                        'severity': 'high' if conflict_type in ['exact', 'word_match'] else 'medium',
                        'resolution': self._get_conflict_resolution(kw_term, neg_term, conflict_type)
                    })
        
        if conflicts:
            logger.warning(f"Found {len(conflicts)} conflicts between keywords and negatives")
        
        return conflicts
    
    def _get_conflict_resolution(self, keyword: str, negative: str, conflict_type: str) -> str:
        """Get recommended resolution for a keyword-negative conflict."""
        if conflict_type == 'exact':
            return f"Remove keyword '{keyword}' as it exactly matches negative keyword"
        elif conflict_type == 'word_match':
            return f"Consider removing keyword '{keyword}' or refining negative '{negative}' to be more specific"
        else:  # partial
            return f"Review if '{keyword}' should be excluded or if negative '{negative}' needs adjustment"
    
    def suggest_additional_negatives(
        self,
        keywords: List[Any],
        existing_negatives: List[NegativeKeyword],
        min_frequency: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Suggest additional negative keywords based on keyword analysis.
        
        Args:
            keywords: List of keywords to analyze
            existing_negatives: Current negative keywords
            min_frequency: Minimum frequency of a pattern to suggest as negative
        
        Returns:
            List of suggested negative keywords with reasons
        """
        suggestions = []
        existing_neg_terms = {neg.term.lower() for neg in existing_negatives}
        
        # Common negative patterns to look for
        negative_patterns = {
            'information_seeking': ['what is', 'how to', 'why does', 'when to', 'guide to'],
            'comparison': ['vs', 'versus', 'comparison', 'difference between', 'better than'],
            'educational': ['learn', 'study', 'course', 'class', 'certification'],
            'research': ['research', 'statistics', 'data', 'report', 'analysis'],
            'location_specific': ['near me', 'nearby', 'closest', 'local'],
            'competitor_brands': []  # Will be detected dynamically
        }
        
        # Count pattern occurrences
        pattern_counts = {}
        brand_mentions = {}
        
        for keyword in keywords:
            # Extract keyword term
            if isinstance(keyword, dict):
                kw_term = keyword.get('keyword', keyword.get('term', ''))
            elif hasattr(keyword, 'keyword'):
                kw_term = keyword.keyword
            elif hasattr(keyword, 'term'):
                kw_term = keyword.term
            else:
                kw_term = str(keyword)
            
            if not kw_term:
                continue
            
            kw_lower = kw_term.lower()
            
            # Check for patterns
            for pattern_type, patterns in negative_patterns.items():
                for pattern in patterns:
                    if pattern in kw_lower:
                        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            # Detect potential brand mentions (capitalized words)
            words = kw_term.split()
            for word in words:
                if word[0].isupper() and len(word) > 3:
                    brand_mentions[word.lower()] = brand_mentions.get(word.lower(), 0) + 1
        
        # Generate suggestions based on frequency
        for pattern, count in pattern_counts.items():
            if count >= min_frequency and pattern not in existing_neg_terms:
                suggestions.append({
                    'term': pattern,
                    'reason': f"Pattern '{pattern}' appears in {count} keywords - likely informational intent",
                    'confidence': min(count / 10, 1.0),  # Confidence based on frequency
                    'count': count
                })
        
        # Suggest frequent brand mentions as negatives (potential competitors)
        for brand, count in brand_mentions.items():
            if count >= min_frequency and brand not in existing_neg_terms:
                # Check if it's not a common word
                common_words = {'repair', 'service', 'plumbing', 'water', 'emergency', 'drain', 'pipe'}
                if brand not in common_words:
                    suggestions.append({
                        'term': brand,
                        'reason': f"Potential competitor brand mentioned {count} times",
                        'confidence': min(count / 15, 1.0),
                        'count': count
                    })
        
        # Sort by confidence and count
        suggestions.sort(key=lambda x: (x['confidence'], x['count']), reverse=True)
        
        logger.info(f"Generated {len(suggestions)} additional negative keyword suggestions")
        return suggestions
    
    def export_for_google_ads(
        self,
        negative_keywords: List[NegativeKeyword],
        campaign_level: bool = True
    ) -> List[Dict[str, str]]:
        """
        Export negative keywords in Google Ads compatible format.
        
        Args:
            negative_keywords: List of negative keywords to export
            campaign_level: Whether to apply at campaign level (True) or ad group level (False)
        
        Returns:
            List of dictionaries ready for CSV export
        """
        export_data = []
        
        for neg in negative_keywords:
            # Convert to Google Ads format based on match type
            if neg.match_type == MatchType.EXACT:
                formatted_keyword = f"[{neg.term}]"
            elif neg.match_type == MatchType.PHRASE:
                formatted_keyword = f'"{neg.term}"'
            else:  # BROAD
                formatted_keyword = neg.term
            
            export_data.append({
                'Negative Keyword': formatted_keyword,
                'Campaign/Ad Group': 'Campaign' if campaign_level else 'Ad group',
                'Match Type': neg.match_type.value if hasattr(neg.match_type, 'value') else neg.match_type,
                'Reason': neg.reason,
                'Auto Generated': 'Yes' if neg.auto_generated else 'No'
            })
        
        return export_data
    
    def export_for_bing_ads(
        self,
        negative_keywords: List[NegativeKeyword]
    ) -> List[Dict[str, str]]:
        """
        Export negative keywords in Bing Ads compatible format.
        
        Args:
            negative_keywords: List of negative keywords to export
        
        Returns:
            List of dictionaries ready for CSV export
        """
        export_data = []
        
        for neg in negative_keywords:
            export_data.append({
                'Keyword Text': neg.term,
                'Match Type': neg.match_type.value.title() if hasattr(neg.match_type, 'value') else 'Phrase',
                'Status': 'Active',
                'Bid': '',  # Not applicable for negative keywords
                'Campaign': '',  # To be filled by user
                'Ad Group': '',  # To be filled by user
                'Reason': neg.reason
            })
        
        return export_data