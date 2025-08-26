#!/usr/bin/env python3
"""
CLI interface for DataForSEO with platform selection (Google Ads, Bing Ads, or both).

Usage examples:
    python cli_dataforseo.py keywords --platform=google --endpoint=search_volume --keywords="marketing,seo"
    python cli_dataforseo.py keywords --platform=both --endpoint=keywords_for_site --url="example.com"
    python cli_dataforseo.py keywords --platform=bing --endpoint=audience_estimation --keywords-file="keywords.csv"
"""

import asyncio
import argparse
import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from api_integration.dataforseo.google_ads_client import GoogleAdsClient
from api_integration.dataforseo.bing_ads_client import BingAdsClient

# Load environment variables
load_dotenv()


class DataForSEOCLI:
    """CLI interface for DataForSEO PPC operations."""
    
    def __init__(self):
        """Initialize CLI with credentials from environment."""
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        
        if not self.login or not self.password:
            print("Error: DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD must be set in .env file")
            sys.exit(1)
    
    def parse_arguments(self) -> argparse.Namespace:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(
            description="DataForSEO CLI for PPC keyword research",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Keywords command
        keywords_parser = subparsers.add_parser(
            "keywords",
            help="Keyword research operations"
        )
        
        keywords_parser.add_argument(
            "--platform",
            choices=["google", "bing", "both"],
            required=True,
            help="Platform to use for keyword data"
        )
        
        keywords_parser.add_argument(
            "--endpoint",
            required=True,
            choices=[
                # Google Ads endpoints
                "search_volume",
                "keywords_for_site",
                "keywords_for_keywords",
                "ad_traffic",
                # Bing Ads endpoints
                "search_volume_history",
                "keyword_performance",
                "keyword_suggestions_url",
                "audience_estimation",
                # Common endpoints
                "locations",
                "languages"
            ],
            help="API endpoint to call"
        )
        
        # Input options
        input_group = keywords_parser.add_mutually_exclusive_group()
        input_group.add_argument(
            "--keywords",
            help="Comma-separated list of keywords"
        )
        input_group.add_argument(
            "--keywords-file",
            help="CSV file containing keywords (one per line or in 'keyword' column)"
        )
        input_group.add_argument(
            "--url",
            help="URL for site-based keyword extraction"
        )
        
        # Optional parameters
        keywords_parser.add_argument(
            "--location",
            type=int,
            default=2840,
            help="Location code (default: 2840 for USA)"
        )
        
        keywords_parser.add_argument(
            "--language",
            default="en",
            help="Language code (default: en)"
        )
        
        keywords_parser.add_argument(
            "--bid",
            type=float,
            help="Max CPC bid for traffic estimates"
        )
        
        keywords_parser.add_argument(
            "--match",
            choices=["exact", "phrase", "broad"],
            default="exact",
            help="Match type for traffic/performance estimates"
        )
        
        keywords_parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum number of results"
        )
        
        keywords_parser.add_argument(
            "--sort-by",
            choices=["search_volume", "cpc", "competition"],
            help="Sort results by metric"
        )
        
        keywords_parser.add_argument(
            "--date-from",
            help="Start date for historical data (YYYY-MM-DD)"
        )
        
        keywords_parser.add_argument(
            "--date-to",
            help="End date for historical data (YYYY-MM-DD)"
        )
        
        keywords_parser.add_argument(
            "--device",
            choices=["desktop", "mobile", "tablet"],
            help="Device type filter (Bing only)"
        )
        
        keywords_parser.add_argument(
            "--exclude-brands",
            action="store_true",
            help="Exclude branded keywords"
        )
        
        # Output options
        keywords_parser.add_argument(
            "--output",
            choices=["json", "csv", "table"],
            default="table",
            help="Output format (default: table)"
        )
        
        keywords_parser.add_argument(
            "--output-file",
            help="Save results to file"
        )
        
        keywords_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed output including all metrics"
        )
        
        # Validate command
        validate_parser = subparsers.add_parser(
            "validate",
            help="Validate API credentials"
        )
        
        validate_parser.add_argument(
            "--platform",
            choices=["google", "bing", "both"],
            default="both",
            help="Platform to validate"
        )
        
        return parser.parse_args()
    
    def load_keywords_from_file(self, filepath: str) -> List[str]:
        """Load keywords from CSV file."""
        keywords = []
        path = Path(filepath)
        
        if not path.exists():
            print(f"Error: File {filepath} not found")
            sys.exit(1)
        
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames and 'keyword' in reader.fieldnames:
                # Has header with 'keyword' column
                for row in reader:
                    if row.get('keyword'):
                        keywords.append(row['keyword'].strip())
            else:
                # Simple list of keywords
                f.seek(0)
                for line in f:
                    keyword = line.strip()
                    if keyword:
                        keywords.append(keyword)
        
        return keywords
    
    async def run_google_ads(
        self,
        endpoint: str,
        keywords: Optional[List[str]] = None,
        url: Optional[str] = None,
        args: argparse.Namespace = None
    ) -> Dict[str, Any]:
        """Run Google Ads endpoint."""
        client = GoogleAdsClient(self.login, self.password)
        
        async with client:
            if endpoint == "search_volume":
                return await client.get_search_volume(
                    keywords=keywords,
                    location_code=args.location,
                    language_code=args.language,
                    date_from=args.date_from,
                    date_to=args.date_to,
                    sort_by=args.sort_by
                )
            
            elif endpoint == "keywords_for_site":
                return await client.get_keywords_for_site(
                    target=url,
                    location_code=args.location,
                    language_code=args.language,
                    include_branded_keywords=not args.exclude_brands,
                    limit=args.limit
                )
            
            elif endpoint == "keywords_for_keywords":
                return await client.get_keywords_for_keywords(
                    keywords=keywords,
                    location_code=args.location,
                    language_code=args.language,
                    limit=args.limit,
                    sort_by=args.sort_by
                )
            
            elif endpoint == "ad_traffic":
                return await client.get_ad_traffic_by_keywords(
                    keywords=keywords,
                    location_code=args.location,
                    language_code=args.language,
                    bid=args.bid,
                    match=args.match,
                    date_from=args.date_from,
                    date_to=args.date_to
                )
            
            elif endpoint == "locations":
                return await client.get_locations()
            
            elif endpoint == "languages":
                return await client.get_languages()
            
            else:
                return {"success": False, "error": f"Endpoint {endpoint} not supported for Google Ads"}
    
    async def run_bing_ads(
        self,
        endpoint: str,
        keywords: Optional[List[str]] = None,
        url: Optional[str] = None,
        args: argparse.Namespace = None
    ) -> Dict[str, Any]:
        """Run Bing Ads endpoint."""
        client = BingAdsClient(self.login, self.password)
        
        async with client:
            if endpoint == "search_volume":
                return await client.get_search_volume(
                    keywords=keywords,
                    location_code=args.location,
                    language_code=args.language,
                    device=args.device,
                    sort_by=args.sort_by
                )
            
            elif endpoint == "search_volume_history":
                return await client.get_search_volume_history(
                    keywords=keywords,
                    location_code=args.location,
                    language_code=args.language,
                    date_from=args.date_from,
                    date_to=args.date_to,
                    device=args.device
                )
            
            elif endpoint == "keywords_for_site":
                return await client.get_keywords_for_site(
                    target=url,
                    location_code=args.location,
                    language_code=args.language,
                    limit=args.limit,
                    sort_by=args.sort_by
                )
            
            elif endpoint == "keywords_for_keywords":
                return await client.get_keywords_for_keywords(
                    keywords=keywords,
                    location_code=args.location,
                    language_code=args.language,
                    limit=args.limit
                )
            
            elif endpoint == "keyword_performance":
                return await client.get_keyword_performance(
                    keywords=keywords,
                    location_code=args.location,
                    language_code=args.language,
                    match=args.match
                )
            
            elif endpoint == "keyword_suggestions_url":
                return await client.get_keyword_suggestions_for_url(
                    target=url,
                    language_code=args.language,
                    exclude_brands=args.exclude_brands,
                    limit=args.limit
                )
            
            elif endpoint == "audience_estimation":
                return await client.get_audience_estimation(
                    keywords=keywords,
                    location_code=args.location,
                    language_code=args.language,
                    bid=args.bid,
                    match=args.match
                )
            
            elif endpoint == "locations":
                return await client.get_locations()
            
            elif endpoint == "languages":
                return await client.get_languages()
            
            else:
                return {"success": False, "error": f"Endpoint {endpoint} not supported for Bing Ads"}
    
    def format_output_table(self, data: List[Dict], platform: str, verbose: bool = False):
        """Format output as table."""
        if not data:
            print("No results found")
            return
        
        print(f"\n{platform} Results:")
        print("-" * 80)
        
        # Determine which fields to show
        if verbose:
            # Show all available fields
            headers = list(data[0].keys())
        else:
            # Show key fields only
            common_fields = ["keyword", "search_volume", "competition", "cpc"]
            headers = [h for h in common_fields if h in data[0]]
        
        # Print header
        header_line = " | ".join(f"{h[:15]:15}" for h in headers)
        print(header_line)
        print("-" * 80)
        
        # Print data rows
        for item in data[:50]:  # Limit to 50 rows for readability
            row = []
            for header in headers:
                value = item.get(header, "")
                if isinstance(value, float):
                    row.append(f"{value:15.2f}")
                elif isinstance(value, int):
                    row.append(f"{value:15d}")
                else:
                    row.append(f"{str(value)[:15]:15}")
            print(" | ".join(row))
        
        if len(data) > 50:
            print(f"\n... and {len(data) - 50} more results")
    
    def save_output(self, data: Dict[str, Any], filepath: str, format: str):
        """Save output to file."""
        path = Path(filepath)
        
        if format == "json":
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        
        elif format == "csv":
            # Flatten the results for CSV
            all_results = []
            
            if "google" in data:
                for item in data["google"].get("data", []):
                    item["platform"] = "Google Ads"
                    all_results.append(item)
            
            if "bing" in data:
                for item in data["bing"].get("data", []):
                    item["platform"] = "Bing Ads"
                    all_results.append(item)
            
            if all_results:
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
                    writer.writeheader()
                    writer.writerows(all_results)
        
        print(f"\nResults saved to {filepath}")
    
    async def validate_credentials(self, platform: str):
        """Validate API credentials."""
        results = {}
        
        if platform in ["google", "both"]:
            client = GoogleAdsClient(self.login, self.password)
            async with client:
                is_valid = await client.validate_credentials()
                results["google"] = "✓ Valid" if is_valid else "✗ Invalid"
        
        if platform in ["bing", "both"]:
            client = BingAdsClient(self.login, self.password)
            async with client:
                is_valid = await client.validate_credentials()
                results["bing"] = "✓ Valid" if is_valid else "✗ Invalid"
        
        print("\nCredentials Validation:")
        print("-" * 40)
        for platform, status in results.items():
            print(f"{platform.capitalize():10} : {status}")
    
    async def run(self):
        """Main entry point for CLI."""
        args = self.parse_arguments()
        
        if args.command == "validate":
            await self.validate_credentials(args.platform)
            return
        
        if args.command == "keywords":
            # Prepare keywords or URL
            keywords = None
            url = None
            
            if args.keywords:
                keywords = [k.strip() for k in args.keywords.split(",")]
            elif args.keywords_file:
                keywords = self.load_keywords_from_file(args.keywords_file)
            elif args.url:
                url = args.url
            else:
                # Check which endpoint to determine required input
                if args.endpoint in ["keywords_for_site", "keyword_suggestions_url"]:
                    print("Error: --url is required for this endpoint")
                else:
                    print("Error: --keywords, --keywords-file, or --url is required")
                sys.exit(1)
            
            # Track results
            results = {}
            
            # Run on selected platforms
            if args.platform in ["google", "both"]:
                print(f"\nRunning Google Ads {args.endpoint}...")
                try:
                    result = await self.run_google_ads(
                        args.endpoint, keywords, url, args
                    )
                    results["google"] = result
                    
                    if args.output == "table" and result.get("success"):
                        self.format_output_table(
                            result.get("data", []),
                            "Google Ads",
                            args.verbose
                        )
                except Exception as e:
                    print(f"Google Ads error: {e}")
                    results["google"] = {"success": False, "error": str(e)}
            
            if args.platform in ["bing", "both"]:
                print(f"\nRunning Bing Ads {args.endpoint}...")
                try:
                    result = await self.run_bing_ads(
                        args.endpoint, keywords, url, args
                    )
                    results["bing"] = result
                    
                    if args.output == "table" and result.get("success"):
                        self.format_output_table(
                            result.get("data", []),
                            "Bing Ads",
                            args.verbose
                        )
                except Exception as e:
                    print(f"Bing Ads error: {e}")
                    results["bing"] = {"success": False, "error": str(e)}
            
            # Save output if requested
            if args.output_file:
                self.save_output(results, args.output_file, args.output)
            elif args.output == "json":
                print("\nJSON Output:")
                print(json.dumps(results, indent=2, default=str))
            
            # Print summary
            print("\n" + "=" * 80)
            print("Summary:")
            for platform, result in results.items():
                if result.get("success"):
                    data_count = len(result.get("data", []))
                    cost = result.get("cost", 0)
                    print(f"{platform.capitalize():10} : {data_count} results (cost: ${cost:.3f})")
                else:
                    print(f"{platform.capitalize():10} : Failed - {result.get('error', 'Unknown error')}")


def main():
    """Main entry point."""
    cli = DataForSEOCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()