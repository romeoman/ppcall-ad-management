"""Tests for DataForSEO CLI interface."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import argparse
import json
import csv
from pathlib import Path
import tempfile
import os

from cli_dataforseo import DataForSEOCLI


class TestDataForSEOCLI:
    """Test suite for DataForSEO CLI."""

    @pytest.fixture
    def cli(self):
        """Create CLI instance with mocked credentials."""
        with patch.dict(os.environ, {
            'DATAFORSEO_LOGIN': 'test_login',
            'DATAFORSEO_PASSWORD': 'test_password'
        }):
            return DataForSEOCLI()

    def test_cli_initialization(self, cli):
        """Test CLI initializes with credentials."""
        assert cli.login == "test_login"
        assert cli.password == "test_password"

    def test_cli_without_credentials(self):
        """Test CLI exits without credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                DataForSEOCLI()

    def test_parse_arguments_google_search_volume(self, cli):
        """Test parsing arguments for Google search volume."""
        test_args = [
            "keywords",
            "--platform", "google",
            "--endpoint", "search_volume",
            "--keywords", "marketing,seo",
            "--location", "2840",
            "--language", "en"
        ]
        
        with patch('sys.argv', ['cli_dataforseo.py'] + test_args):
            args = cli.parse_arguments()
            assert args.command == "keywords"
            assert args.platform == "google"
            assert args.endpoint == "search_volume"
            assert args.keywords == "marketing,seo"

    def test_parse_arguments_both_platforms(self, cli):
        """Test parsing arguments for both platforms."""
        test_args = [
            "keywords",
            "--platform", "both",
            "--endpoint", "keywords_for_site",
            "--url", "example.com",
            "--output", "json"
        ]
        
        with patch('sys.argv', ['cli_dataforseo.py'] + test_args):
            args = cli.parse_arguments()
            assert args.platform == "both"
            assert args.endpoint == "keywords_for_site"
            assert args.url == "example.com"

    def test_load_keywords_from_csv(self, cli):
        """Test loading keywords from CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("keyword\n")
            f.write("marketing software\n")
            f.write("email marketing\n")
            f.write("seo tools\n")
            temp_path = f.name
        
        try:
            keywords = cli.load_keywords_from_file(temp_path)
            assert len(keywords) == 3
            assert "marketing software" in keywords
            assert "email marketing" in keywords
            assert "seo tools" in keywords
        finally:
            Path(temp_path).unlink()

    def test_load_keywords_from_simple_list(self, cli):
        """Test loading keywords from simple text file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("keyword one\n")
            f.write("keyword two\n")
            f.write("keyword three\n")
            temp_path = f.name
        
        try:
            keywords = cli.load_keywords_from_file(temp_path)
            assert len(keywords) == 3
            assert "keyword one" in keywords
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_run_google_ads_search_volume(self, cli):
        """Test running Google Ads search volume endpoint."""
        mock_args = MagicMock()
        mock_args.location = 2840
        mock_args.language = "en"
        mock_args.date_from = None
        mock_args.date_to = None
        mock_args.sort_by = None
        
        with patch('cli_dataforseo.GoogleAdsClient') as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_instance.get_search_volume = AsyncMock(return_value={
                "success": True,
                "data": [{"keyword": "test", "search_volume": 1000}]
            })
            
            result = await cli.run_google_ads(
                "search_volume",
                keywords=["test"],
                args=mock_args
            )
            
            assert result["success"] is True
            assert len(result["data"]) == 1
            mock_instance.get_search_volume.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_bing_ads_audience_estimation(self, cli):
        """Test running Bing Ads audience estimation."""
        mock_args = MagicMock()
        mock_args.location = 2840
        mock_args.language = "en"
        mock_args.bid = 10.0
        mock_args.match = "exact"
        
        with patch('cli_dataforseo.BingAdsClient') as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_instance.get_audience_estimation = AsyncMock(return_value={
                "success": True,
                "data": [{"audience_size": 1000000}]
            })
            
            result = await cli.run_bing_ads(
                "audience_estimation",
                keywords=["test"],
                args=mock_args
            )
            
            assert result["success"] is True
            assert result["data"][0]["audience_size"] == 1000000

    def test_format_output_table(self, cli, capsys):
        """Test formatting output as table."""
        data = [
            {"keyword": "test1", "search_volume": 1000, "cpc": 2.5, "competition": 0.75},
            {"keyword": "test2", "search_volume": 2000, "cpc": 3.5, "competition": 0.85}
        ]
        
        cli.format_output_table(data, "Test Platform")
        captured = capsys.readouterr()
        
        assert "Test Platform Results:" in captured.out
        assert "keyword" in captured.out
        assert "test1" in captured.out
        assert "1000" in captured.out

    def test_save_output_json(self, cli):
        """Test saving output as JSON."""
        data = {
            "google": {
                "success": True,
                "data": [{"keyword": "test", "volume": 1000}]
            }
        }
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            cli.save_output(data, temp_path, "json")
            
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["google"]["success"] is True
            assert saved_data["google"]["data"][0]["keyword"] == "test"
        finally:
            Path(temp_path).unlink()

    def test_save_output_csv(self, cli):
        """Test saving output as CSV."""
        data = {
            "google": {
                "success": True,
                "data": [
                    {"keyword": "test1", "volume": 1000},
                    {"keyword": "test2", "volume": 2000}
                ]
            },
            "bing": {
                "success": True,
                "data": [
                    {"keyword": "test3", "volume": 3000}
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            cli.save_output(data, temp_path, "csv")
            
            with open(temp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 3
            assert rows[0]["platform"] == "Google Ads"
            assert rows[2]["platform"] == "Bing Ads"
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_validate_credentials(self, cli, capsys):
        """Test credential validation."""
        with patch('cli_dataforseo.GoogleAdsClient') as MockGoogle, \
             patch('cli_dataforseo.BingAdsClient') as MockBing:
            
            # Mock Google client
            mock_google = MockGoogle.return_value
            mock_google.__aenter__ = AsyncMock(return_value=mock_google)
            mock_google.__aexit__ = AsyncMock()
            mock_google.validate_credentials = AsyncMock(return_value=True)
            
            # Mock Bing client
            mock_bing = MockBing.return_value
            mock_bing.__aenter__ = AsyncMock(return_value=mock_bing)
            mock_bing.__aexit__ = AsyncMock()
            mock_bing.validate_credentials = AsyncMock(return_value=True)
            
            await cli.validate_credentials("both")
            
            captured = capsys.readouterr()
            assert "✓ Valid" in captured.out
            assert "Google" in captured.out
            assert "Bing" in captured.out

    @pytest.mark.asyncio
    async def test_run_with_both_platforms(self, cli):
        """Test running CLI with both platforms selected."""
        mock_args = [
            "keywords",
            "--platform", "both",
            "--endpoint", "search_volume",
            "--keywords", "test",
            "--output", "json"
        ]
        
        with patch('sys.argv', ['cli_dataforseo.py'] + mock_args), \
             patch('cli_dataforseo.GoogleAdsClient') as MockGoogle, \
             patch('cli_dataforseo.BingAdsClient') as MockBing:
            
            # Mock Google client
            mock_google = MockGoogle.return_value
            mock_google.__aenter__ = AsyncMock(return_value=mock_google)
            mock_google.__aexit__ = AsyncMock()
            mock_google.get_search_volume = AsyncMock(return_value={
                "success": True,
                "data": [{"keyword": "test", "search_volume": 1000}],
                "cost": 0.005
            })
            
            # Mock Bing client
            mock_bing = MockBing.return_value
            mock_bing.__aenter__ = AsyncMock(return_value=mock_bing)
            mock_bing.__aexit__ = AsyncMock()
            mock_bing.get_search_volume = AsyncMock(return_value={
                "success": True,
                "data": [{"keyword": "test", "search_volume": 800}],
                "cost": 0.004
            })
            
            with patch('builtins.print'):
                await cli.run()
            
            mock_google.get_search_volume.assert_called_once()
            mock_bing.get_search_volume.assert_called_once()