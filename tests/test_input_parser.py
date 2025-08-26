"""
Unit tests for input parser module
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from src.input_parser import (
    parse_seed_keywords,
    parse_categories,
    parse_locations,
    parse_spyfu_data,
    parse_competitor_urls,
    parse_negative_keywords
)


class TestSeedKeywordsParser:
    """Test cases for parse_seed_keywords function"""
    
    def test_parse_csv_with_categories(self, tmp_path):
        """Test parsing CSV with keyword and category columns"""
        csv_file = tmp_path / "keywords.csv"
        csv_content = """Keyword,Category
plumber near me,emergency
emergency plumber,emergency
drain cleaning,services
pipe repair,services"""
        csv_file.write_text(csv_content)
        
        result = parse_seed_keywords(str(csv_file))
        
        assert len(result) == 4
        assert result[0] == {'keyword': 'plumber near me', 'category': 'emergency'}
        assert result[2] == {'keyword': 'drain cleaning', 'category': 'services'}
    
    def test_parse_csv_without_categories(self, tmp_path):
        """Test parsing CSV with only keyword column"""
        csv_file = tmp_path / "keywords.csv"
        csv_content = """Keyword
plumber near me
emergency plumber
drain cleaning"""
        csv_file.write_text(csv_content)
        
        result = parse_seed_keywords(str(csv_file))
        
        assert len(result) == 3
        assert all(item['category'] == 'general' for item in result)
        assert result[0]['keyword'] == 'plumber near me'
    
    def test_parse_txt_file(self, tmp_path):
        """Test parsing TXT file with one keyword per line"""
        txt_file = tmp_path / "keywords.txt"
        txt_content = """plumber near me
emergency plumber
drain cleaning
pipe repair"""
        txt_file.write_text(txt_content)
        
        result = parse_seed_keywords(str(txt_file))
        
        assert len(result) == 4
        assert all(item['category'] == 'general' for item in result)
        assert result[1]['keyword'] == 'emergency plumber'
    
    def test_skip_empty_lines(self, tmp_path):
        """Test that empty lines are skipped"""
        txt_file = tmp_path / "keywords.txt"
        txt_content = """plumber near me

emergency plumber

drain cleaning"""
        txt_file.write_text(txt_content)
        
        result = parse_seed_keywords(str(txt_file))
        
        assert len(result) == 3
    
    def test_file_not_found(self):
        """Test error handling for non-existent file"""
        with pytest.raises(FileNotFoundError):
            parse_seed_keywords("nonexistent.txt")
    
    def test_unsupported_format(self, tmp_path):
        """Test error for unsupported file format"""
        json_file = tmp_path / "keywords.json"
        json_file.write_text('{"keywords": []}')
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            parse_seed_keywords(str(json_file))
    
    def test_empty_file(self, tmp_path):
        """Test error for empty file"""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        
        with pytest.raises(ValueError, match="No valid keywords"):
            parse_seed_keywords(str(empty_file))


class TestCategoriesParser:
    """Test cases for parse_categories function"""
    
    def test_parse_categories_with_description(self, tmp_path):
        """Test parsing categories CSV with descriptions"""
        csv_file = tmp_path / "categories.csv"
        csv_content = """Category,Description
Emergency,24/7 emergency services
Residential,Home plumbing services
Commercial,Business plumbing solutions"""
        csv_file.write_text(csv_content)
        
        result = parse_categories(str(csv_file))
        
        assert len(result) == 3
        assert result[0] == {'name': 'Emergency', 'description': '24/7 emergency services'}
        assert result[2]['name'] == 'Commercial'
    
    def test_parse_categories_without_description(self, tmp_path):
        """Test parsing categories CSV without description column"""
        csv_file = tmp_path / "categories.csv"
        csv_content = """Name
Emergency
Residential
Commercial"""
        csv_file.write_text(csv_content)
        
        result = parse_categories(str(csv_file))
        
        assert len(result) == 3
        assert result[0] == {'name': 'Emergency'}
        assert 'description' not in result[0]
    
    def test_file_not_found(self):
        """Test error handling for non-existent file"""
        with pytest.raises(FileNotFoundError):
            parse_categories("nonexistent.csv")
    
    def test_non_csv_format(self, tmp_path):
        """Test error for non-CSV format"""
        txt_file = tmp_path / "categories.txt"
        txt_file.write_text("Emergency")
        
        with pytest.raises(ValueError, match="must be in CSV format"):
            parse_categories(str(txt_file))


class TestLocationsParser:
    """Test cases for parse_locations function"""
    
    def test_parse_locations_full_data(self, tmp_path):
        """Test parsing locations with city, state, and zip"""
        csv_file = tmp_path / "locations.csv"
        csv_content = """City,State,Zip
Los Angeles,CA,90001
San Francisco,CA,94102
New York,NY,10001"""
        csv_file.write_text(csv_content)
        
        result = parse_locations(str(csv_file))
        
        assert len(result) == 3
        assert result[0] == {'city': 'Los Angeles', 'state': 'CA', 'zip': '90001'}
        assert result[1]['zip'] == '94102'
    
    def test_parse_locations_zip_only(self, tmp_path):
        """Test parsing locations with only zip codes"""
        csv_file = tmp_path / "locations.csv"
        csv_content = """Zip Code
90001
94102
10001"""
        csv_file.write_text(csv_content)
        
        result = parse_locations(str(csv_file))
        
        assert len(result) == 3
        assert result[0] == {'zip': '90001'}
    
    def test_zip_padding(self, tmp_path):
        """Test that zip codes are padded to 5 digits"""
        csv_file = tmp_path / "locations.csv"
        csv_content = """Zip
1234
90001"""
        csv_file.write_text(csv_content)
        
        result = parse_locations(str(csv_file))
        
        assert result[0]['zip'] == '01234'
        assert result[1]['zip'] == '90001'
    
    def test_missing_required_columns(self, tmp_path):
        """Test error when neither city nor zip columns exist"""
        csv_file = tmp_path / "locations.csv"
        csv_content = """State,Country
CA,USA
NY,USA"""
        csv_file.write_text(csv_content)
        
        with pytest.raises(ValueError, match="must contain at least"):
            parse_locations(str(csv_file))


class TestSpyFuParser:
    """Test cases for parse_spyfu_data function"""
    
    def test_parse_spyfu_with_metrics(self, tmp_path):
        """Test parsing SpyFu CSV with various metrics"""
        csv_file = tmp_path / "spyfu.csv"
        csv_content = """Keyword,Search Volume,CPC,SEO Difficulty,Clicks
plumber near me,10000,$5.50,45,2500
emergency plumber,8000,$8.25,52,1800"""
        csv_file.write_text(csv_content)
        
        result = parse_spyfu_data(str(csv_file))
        
        assert result['source'] == 'spyfu'
        assert result['total_keywords'] == 2
        assert 'keyword' in result['columns_found']
        assert 'volume' in result['columns_found']
        assert 'cpc' in result['columns_found']
        
        keywords = result['keywords']
        assert keywords[0]['keyword'] == 'plumber near me'
        assert keywords[0]['volume'] == 10000
        assert keywords[0]['cpc'] == 5.50
        assert keywords[1]['cpc'] == 8.25
    
    def test_parse_spyfu_minimal(self, tmp_path):
        """Test parsing SpyFu CSV with only keyword column"""
        csv_file = tmp_path / "spyfu.csv"
        csv_content = """Keyword
plumber near me
emergency plumber"""
        csv_file.write_text(csv_content)
        
        result = parse_spyfu_data(str(csv_file))
        
        assert result['total_keywords'] == 2
        assert result['columns_found'] == ['keyword']
        assert len(result['keywords']) == 2
    
    def test_missing_keyword_column(self, tmp_path):
        """Test error when keyword column is missing"""
        csv_file = tmp_path / "spyfu.csv"
        csv_content = """Volume,CPC
10000,$5.50
8000,$8.25"""
        csv_file.write_text(csv_content)
        
        with pytest.raises(ValueError, match="must contain a keyword column"):
            parse_spyfu_data(str(csv_file))


class TestCompetitorUrlsParser:
    """Test cases for parse_competitor_urls function"""
    
    def test_parse_valid_urls(self, tmp_path):
        """Test parsing valid URLs"""
        txt_file = tmp_path / "urls.txt"
        txt_content = """https://example.com/plumbing
http://competitor.com
www.anothersite.com
plumbersite.com"""
        txt_file.write_text(txt_content)
        
        result = parse_competitor_urls(str(txt_file))
        
        assert len(result) == 4
        assert result[0] == 'https://example.com/plumbing'
        assert result[1] == 'http://competitor.com'
        assert result[2] == 'https://www.anothersite.com'  # https added
        assert result[3] == 'https://plumbersite.com'  # https added
    
    def test_skip_comments_and_empty_lines(self, tmp_path):
        """Test that comments and empty lines are skipped"""
        txt_file = tmp_path / "urls.txt"
        txt_content = """# Comment line
https://example.com

http://competitor.com
# Another comment
"""
        txt_file.write_text(txt_content)
        
        result = parse_competitor_urls(str(txt_file))
        
        assert len(result) == 2
        assert result[0] == 'https://example.com'
        assert result[1] == 'http://competitor.com'
    
    def test_non_txt_format(self, tmp_path):
        """Test error for non-TXT format"""
        csv_file = tmp_path / "urls.csv"
        csv_file.write_text("url\nhttps://example.com")
        
        with pytest.raises(ValueError, match="must be in TXT format"):
            parse_competitor_urls(str(csv_file))
    
    def test_empty_file(self, tmp_path):
        """Test error for file with no valid URLs"""
        txt_file = tmp_path / "empty.txt"
        txt_file.write_text("# Just comments\n\n")
        
        with pytest.raises(ValueError, match="No valid URLs"):
            parse_competitor_urls(str(txt_file))


class TestNegativeKeywordsParser:
    """Test cases for parse_negative_keywords function"""
    
    def test_parse_txt_negative_keywords(self, tmp_path):
        """Test parsing negative keywords from TXT file"""
        txt_file = tmp_path / "negative.txt"
        txt_content = """free
cheap
diy
# Comment
tutorial"""
        txt_file.write_text(txt_content)
        
        result = parse_negative_keywords(str(txt_file))
        
        assert len(result) == 4  # Comment is skipped, but we have 4 valid keywords
        assert 'free' in result
        assert 'cheap' in result
        assert 'diy' in result
        assert 'tutorial' in result
        assert '# Comment' not in result
    
    def test_parse_csv_negative_keywords(self, tmp_path):
        """Test parsing negative keywords from CSV file"""
        csv_file = tmp_path / "negative.csv"
        csv_content = """Negative Keyword
free
cheap
diy"""
        csv_file.write_text(csv_content)
        
        result = parse_negative_keywords(str(csv_file))
        
        assert len(result) == 3
        assert 'free' in result
        assert 'cheap' in result
    
    def test_csv_without_keyword_column(self, tmp_path):
        """Test CSV without explicit keyword column uses first column"""
        csv_file = tmp_path / "negative.csv"
        csv_content = """Terms
free
cheap"""
        csv_file.write_text(csv_content)
        
        result = parse_negative_keywords(str(csv_file))
        
        assert len(result) == 2
        assert 'free' in result
    
    def test_file_not_found(self):
        """Test error handling for non-existent file"""
        with pytest.raises(FileNotFoundError):
            parse_negative_keywords("nonexistent.txt")
    
    def test_unsupported_format(self, tmp_path):
        """Test error for unsupported file format"""
        json_file = tmp_path / "negative.json"
        json_file.write_text('{"keywords": []}')
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            parse_negative_keywords(str(json_file))