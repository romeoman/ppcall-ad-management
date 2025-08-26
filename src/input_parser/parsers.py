"""
Parser functions for various input file formats
"""

import csv
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def parse_seed_keywords(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse seed keywords from a CSV or TXT file.
    
    Args:
        file_path: Path to the seed keywords file (CSV or TXT)
        
    Returns:
        List of dictionaries with 'keyword' and 'category' keys
        
    Raises:
        ValueError: If file format is not supported or data is malformed
        FileNotFoundError: If the file doesn't exist
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Seed keywords file not found: {file_path}")
    
    keywords = []
    
    if file_path.suffix.lower() == '.csv':
        try:
            df = pd.read_csv(file_path)
            
            # Check for expected columns (case-insensitive)
            df.columns = df.columns.str.strip()
            columns_lower = [col.lower() for col in df.columns]
            
            if 'keyword' not in columns_lower:
                raise ValueError("CSV must contain 'Keyword' column")
            
            # Find the actual column names
            keyword_col = df.columns[columns_lower.index('keyword')]
            category_col = None
            
            if 'category' in columns_lower:
                category_col = df.columns[columns_lower.index('category')]
            
            # Process rows
            for _, row in df.iterrows():
                keyword = str(row[keyword_col]).strip()
                if keyword and keyword.lower() != 'nan':
                    category = 'general'
                    if category_col and pd.notna(row[category_col]):
                        category = str(row[category_col]).strip()
                    
                    keywords.append({
                        'keyword': keyword,
                        'category': category
                    })
            
            logger.info(f"Parsed {len(keywords)} seed keywords from CSV")
            
        except Exception as e:
            logger.error(f"Error parsing seed keywords CSV: {e}")
            raise ValueError(f"Failed to parse CSV file: {e}")
            
    elif file_path.suffix.lower() == '.txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    keyword = line.strip()
                    if keyword:  # Skip empty lines
                        keywords.append({
                            'keyword': keyword,
                            'category': 'general'
                        })
            
            logger.info(f"Parsed {len(keywords)} seed keywords from TXT")
            
        except Exception as e:
            logger.error(f"Error parsing seed keywords TXT: {e}")
            raise ValueError(f"Failed to parse TXT file: {e}")
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}. Use CSV or TXT")
    
    if not keywords:
        raise ValueError("No valid keywords found in the file")
    
    return keywords


def parse_categories(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse categories from a CSV file.
    
    Args:
        file_path: Path to the categories CSV file
        
    Returns:
        List of dictionaries with category information
        
    Raises:
        ValueError: If file format is invalid or required columns are missing
        FileNotFoundError: If the file doesn't exist
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Categories file not found: {file_path}")
    
    if file_path.suffix.lower() != '.csv':
        raise ValueError("Categories file must be in CSV format")
    
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        columns_lower = [col.lower() for col in df.columns]
        
        # Check for required columns
        if 'category' not in columns_lower and 'name' not in columns_lower:
            raise ValueError("CSV must contain 'Category' or 'Name' column")
        
        # Find actual column names
        category_col = None
        if 'category' in columns_lower:
            category_col = df.columns[columns_lower.index('category')]
        elif 'name' in columns_lower:
            category_col = df.columns[columns_lower.index('name')]
        
        description_col = None
        if 'description' in columns_lower:
            description_col = df.columns[columns_lower.index('description')]
        
        categories = []
        for _, row in df.iterrows():
            if pd.notna(row[category_col]):
                category = {
                    'name': str(row[category_col]).strip(),
                }
                
                if description_col and pd.notna(row[description_col]):
                    category['description'] = str(row[description_col]).strip()
                
                categories.append(category)
        
        logger.info(f"Parsed {len(categories)} categories")
        return categories
        
    except Exception as e:
        logger.error(f"Error parsing categories CSV: {e}")
        raise ValueError(f"Failed to parse categories file: {e}")


def parse_locations(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse locations from a CSV file.
    
    Args:
        file_path: Path to the locations CSV file
        
    Returns:
        List of dictionaries with location information
        
    Raises:
        ValueError: If file format is invalid or required columns are missing
        FileNotFoundError: If the file doesn't exist
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Locations file not found: {file_path}")
    
    if file_path.suffix.lower() != '.csv':
        raise ValueError("Locations file must be in CSV format")
    
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        columns_lower = [col.lower() for col in df.columns]
        
        # Find column names (flexible mapping)
        city_col = None
        state_col = None
        zip_col = None
        
        for idx, col in enumerate(columns_lower):
            if 'city' in col:
                city_col = df.columns[idx]
            elif 'state' in col:
                state_col = df.columns[idx]
            elif 'zip' in col or 'postal' in col:
                zip_col = df.columns[idx]
        
        if not city_col and not zip_col:
            raise ValueError("CSV must contain at least 'City' or 'Zip' column")
        
        locations = []
        for _, row in df.iterrows():
            location = {}
            
            if city_col and pd.notna(row[city_col]):
                location['city'] = str(row[city_col]).strip()
            
            if state_col and pd.notna(row[state_col]):
                location['state'] = str(row[state_col]).strip()
            
            if zip_col and pd.notna(row[zip_col]):
                # Convert zip to string and ensure it's properly formatted
                zip_code = str(row[zip_col]).strip()
                if zip_code and zip_code != 'nan':
                    # Remove decimal if present (Excel sometimes adds .0)
                    zip_code = zip_code.split('.')[0]
                    location['zip'] = zip_code.zfill(5)  # Ensure 5 digits for US zip codes
            
            if location:  # Only add if at least one field is present
                locations.append(location)
        
        logger.info(f"Parsed {len(locations)} locations")
        return locations
        
    except Exception as e:
        logger.error(f"Error parsing locations CSV: {e}")
        raise ValueError(f"Failed to parse locations file: {e}")


def parse_spyfu_data(file_path: str) -> Dict[str, Any]:
    """
    Parse SpyFu competition data from a CSV file.
    
    Args:
        file_path: Path to the SpyFu CSV export
        
    Returns:
        Dictionary containing parsed SpyFu data with keywords and metrics
        
    Raises:
        ValueError: If file format is invalid or required columns are missing
        FileNotFoundError: If the file doesn't exist
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"SpyFu file not found: {file_path}")
    
    if file_path.suffix.lower() != '.csv':
        raise ValueError("SpyFu file must be in CSV format")
    
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        
        # Common SpyFu column mappings
        column_mapping = {
            'keyword': ['keyword', 'keywords', 'term', 'search term'],
            'volume': ['volume', 'monthly searches', 'search volume', 'searches/month'],
            'cpc': ['cpc', 'cost per click', 'avg cpc'],
            'difficulty': ['difficulty', 'seo difficulty', 'keyword difficulty', 'kd'],
            'clicks': ['clicks', 'monthly clicks', 'est clicks'],
            'position': ['position', 'rank', 'ranking', 'avg position']
        }
        
        # Find actual columns
        parsed_columns = {}
        columns_lower = [col.lower() for col in df.columns]
        
        for key, possible_names in column_mapping.items():
            for name in possible_names:
                for idx, col in enumerate(columns_lower):
                    if name in col:
                        parsed_columns[key] = df.columns[idx]
                        break
                if key in parsed_columns:
                    break
        
        if 'keyword' not in parsed_columns:
            raise ValueError("SpyFu CSV must contain a keyword column")
        
        # Parse data
        keywords = []
        for _, row in df.iterrows():
            if pd.notna(row[parsed_columns['keyword']]):
                keyword_data = {
                    'keyword': str(row[parsed_columns['keyword']]).strip()
                }
                
                # Add optional metrics if available
                for metric in ['volume', 'cpc', 'difficulty', 'clicks', 'position']:
                    if metric in parsed_columns and pd.notna(row[parsed_columns[metric]]):
                        try:
                            value = row[parsed_columns[metric]]
                            if metric == 'cpc':
                                # Remove $ sign if present
                                value = str(value).replace('$', '').replace(',', '')
                            keyword_data[metric] = float(value)
                        except (ValueError, TypeError):
                            logger.warning(f"Could not parse {metric} for keyword: {keyword_data['keyword']}")
                
                keywords.append(keyword_data)
        
        result = {
            'source': 'spyfu',
            'total_keywords': len(keywords),
            'columns_found': list(parsed_columns.keys()),
            'keywords': keywords
        }
        
        logger.info(f"Parsed {len(keywords)} keywords from SpyFu data")
        return result
        
    except Exception as e:
        logger.error(f"Error parsing SpyFu CSV: {e}")
        raise ValueError(f"Failed to parse SpyFu file: {e}")


def parse_competitor_urls(file_path: str) -> List[str]:
    """
    Parse competitor URLs from a TXT file.
    
    Args:
        file_path: Path to the competitor URLs TXT file
        
    Returns:
        List of validated URLs
        
    Raises:
        ValueError: If file format is invalid or URLs are malformed
        FileNotFoundError: If the file doesn't exist
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Competitor URLs file not found: {file_path}")
    
    if file_path.suffix.lower() != '.txt':
        raise ValueError("Competitor URLs file must be in TXT format")
    
    urls = []
    invalid_urls = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                url = line.strip()
                if not url or url.startswith('#'):  # Skip empty lines and comments
                    continue
                
                # Basic URL validation
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                try:
                    parsed = urlparse(url)
                    if parsed.netloc:  # Check if URL has a domain
                        urls.append(url)
                    else:
                        invalid_urls.append((line_num, url))
                except Exception:
                    invalid_urls.append((line_num, url))
        
        if invalid_urls:
            logger.warning(f"Found {len(invalid_urls)} invalid URLs: {invalid_urls[:5]}")
        
        if not urls:
            raise ValueError("No valid URLs found in the file")
        
        logger.info(f"Parsed {len(urls)} valid competitor URLs")
        return urls
        
    except Exception as e:
        logger.error(f"Error parsing competitor URLs: {e}")
        raise ValueError(f"Failed to parse URLs file: {e}")


def parse_negative_keywords(file_path: str) -> List[str]:
    """
    Parse negative keywords from a TXT or CSV file.
    
    Args:
        file_path: Path to the negative keywords file
        
    Returns:
        List of negative keywords
        
    Raises:
        ValueError: If file format is not supported
        FileNotFoundError: If the file doesn't exist
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Negative keywords file not found: {file_path}")
    
    negative_keywords = []
    
    if file_path.suffix.lower() == '.txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    keyword = line.strip()
                    if keyword and not keyword.startswith('#'):  # Skip empty lines and comments
                        negative_keywords.append(keyword)
            
            logger.info(f"Parsed {len(negative_keywords)} negative keywords from TXT")
            
        except Exception as e:
            logger.error(f"Error parsing negative keywords TXT: {e}")
            raise ValueError(f"Failed to parse TXT file: {e}")
            
    elif file_path.suffix.lower() == '.csv':
        try:
            df = pd.read_csv(file_path)
            
            # Try to find keyword column
            df.columns = df.columns.str.strip()
            columns_lower = [col.lower() for col in df.columns]
            
            keyword_col = None
            for idx, col in enumerate(columns_lower):
                if 'keyword' in col or 'negative' in col:
                    keyword_col = df.columns[idx]
                    break
            
            if not keyword_col:
                # If no keyword column, use the first column
                keyword_col = df.columns[0]
            
            for value in df[keyword_col]:
                if pd.notna(value):
                    keyword = str(value).strip()
                    if keyword:
                        negative_keywords.append(keyword)
            
            logger.info(f"Parsed {len(negative_keywords)} negative keywords from CSV")
            
        except Exception as e:
            logger.error(f"Error parsing negative keywords CSV: {e}")
            raise ValueError(f"Failed to parse CSV file: {e}")
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}. Use TXT or CSV")
    
    if not negative_keywords:
        raise ValueError("No valid negative keywords found in the file")
    
    return negative_keywords