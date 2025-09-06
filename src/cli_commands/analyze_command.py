"""Implementation of the 'analyze' CLI command."""

import logging
import asyncio
from pathlib import Path
import os
from typing import List, Optional

from src.project_manager.project_manager import ProjectManager
from src.processors.competition_analyzer import CompetitionAnalyzer
from src.processors.landing_page_scraper import LandingPageScraper
from api_integration.dataforseo.google_ads_client import GoogleAdsClient
from api_integration.firecrawl_client import FireCrawlClient
from src.input_parser.parsers import parse_competitor_urls, parse_spyfu_data
from src.output_generator.csv_exporter import CSVExporter
from models.competition_models import CompetitorAnalysis

logger = logging.getLogger(__name__)


async def execute_analyze(args, project_manager: ProjectManager) -> int:
    """
    Execute the analyze command for competition analysis.
    
    Args:
        args: Command line arguments
        project_manager: ProjectManager instance
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Get project path
        project_path = project_manager.get_project_path(args.project)
        if not project_path:
            logger.error(f"Project '{args.project}' not found")
            return 1
        
        logger.info(f"Analyzing competition for project '{args.project}'")
        
        # Initialize API clients
        google_ads_client = GoogleAdsClient(
            login=os.getenv('DATAFORSEO_LOGIN'),
            password=os.getenv('DATAFORSEO_PASSWORD')
        )
        
        firecrawl_client = None
        if os.getenv('FIRECRAWL_API_KEY'):
            firecrawl_client = FireCrawlClient(
                api_key=os.getenv('FIRECRAWL_API_KEY')
            )
        
        # Initialize analyzer
        cache_dir = project_path / ".cache" / "competition"
        analyzer = CompetitionAnalyzer(
            google_ads_client=google_ads_client,
            cache_dir=cache_dir
        )
        
        # Load competitor URLs
        competitor_urls_file = args.competitors or str(project_path / "inputs" / "competitors" / "competitor_urls.txt")
        competitor_urls = []
        
        if Path(competitor_urls_file).exists():
            competitor_urls = parse_competitor_urls(competitor_urls_file)
            logger.info(f"Loaded {len(competitor_urls)} competitor URLs")
        else:
            logger.warning(f"Competitor URLs file not found: {competitor_urls_file}")
        
        # Load SpyFu data if available
        spyfu_file = args.spyfu or str(project_path / "inputs" / "competitors" / "spyfu_export.csv")
        spyfu_data = None
        
        if Path(spyfu_file).exists():
            spyfu_data = parse_spyfu_data(spyfu_file)
            logger.info(f"Loaded SpyFu data with {spyfu_data['total_keywords']} keywords")
        
        # Analyze competitors
        competitors = []
        all_competitor_keywords = []
        
        print(f"\n🔍 Analyzing {len(competitor_urls)} competitors...")
        
        for i, url in enumerate(competitor_urls, 1):
            print(f"  [{i}/{len(competitor_urls)}] Analyzing {url}...")
            try:
                # Analyze using DataForSEO Keywords for Site API
                competitor = await analyzer.analyze_competitor_website(
                    competitor_url=url,
                    location_code=args.location_code if hasattr(args, 'location_code') else 2840,
                    limit=args.keyword_limit if hasattr(args, 'keyword_limit') else 500
                )
                competitors.append(competitor)
                
                # Store keywords (they're cached in analyzer._competitor_keywords)
                if hasattr(analyzer, '_competitor_keywords'):
                    all_competitor_keywords.extend(analyzer._competitor_keywords)
                
                print(f"       ✓ Found {competitor.organic_keywords} organic + "
                     f"{competitor.paid_keywords} paid keywords")
                
            except Exception as e:
                logger.error(f"Failed to analyze {url}: {e}")
                print(f"       ✗ Error: {e}")
        
        # Process SpyFu data if available
        if spyfu_data:
            print(f"\n📊 Processing SpyFu data...")
            spyfu_keywords = analyzer.process_spyfu_data(spyfu_data)
            all_competitor_keywords.extend(spyfu_keywords)
            print(f"   ✓ Processed {len(spyfu_keywords)} SpyFu keywords")
        
        # Load our keywords for gap analysis
        our_keywords = []
        our_keywords_file = project_path / "outputs" / "keywords" / "expanded_keywords.csv"
        
        if our_keywords_file.exists():
            # Load our keywords from previous research
            import pandas as pd
            df = pd.read_csv(our_keywords_file)
            if 'keyword' in df.columns:
                our_keywords = df['keyword'].tolist()
            elif 'Keyword' in df.columns:
                our_keywords = df['Keyword'].tolist()
            logger.info(f"Loaded {len(our_keywords)} of our keywords for gap analysis")
        
        # Identify keyword gaps
        print(f"\n🎯 Identifying keyword gaps...")
        keyword_gaps = analyzer.identify_keyword_gaps(
            our_keywords=our_keywords,
            competitor_keywords=all_competitor_keywords,
            our_domain=args.our_domain if hasattr(args, 'our_domain') else "our-site.com"
        )
        print(f"   ✓ Found {len(keyword_gaps)} keyword gaps")
        
        # Calculate opportunity scores
        scored_gaps = analyzer.calculate_opportunity_scores(keyword_gaps)
        top_opportunities = [gap for gap, score in scored_gaps[:10]]
        
        # Scrape landing pages if requested
        scraped_pages = []
        if args.scrape_pages and firecrawl_client:
            print(f"\n📄 Scraping competitor landing pages...")
            landing_scraper = LandingPageScraper(firecrawl_client)
            
            # Get URLs to scrape (limit to avoid excessive API calls)
            urls_to_scrape = competitor_urls[:args.max_scrape if hasattr(args, 'max_scrape') else 5]
            scraped_pages = await analyzer.scrape_competitor_landing_pages(
                urls=urls_to_scrape,
                max_concurrent=3
            )
            
            successful = len([s for s in scraped_pages if s.scrape_success])
            print(f"   ✓ Successfully scraped {successful}/{len(urls_to_scrape)} pages")
        
        # Generate comprehensive analysis
        print(f"\n📈 Generating competition analysis report...")
        analysis = analyzer.generate_competitor_analysis(
            our_domain=args.our_domain if hasattr(args, 'our_domain') else "our-site.com",
            competitors=competitors,
            competitor_keywords=all_competitor_keywords,
            keyword_gaps=keyword_gaps,
            scraped_pages=scraped_pages
        )
        
        # Export results
        output_dir = project_path / "outputs" / "competition"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        csv_exporter = CSVExporter(str(output_dir))
        
        # Export keyword gaps
        gaps_file = csv_exporter.export_competition_gaps(keyword_gaps)
        print(f"   ✓ Keyword gaps exported to {gaps_file}")
        
        # Export competitor keywords
        if all_competitor_keywords:
            comp_keywords_file = csv_exporter.export_competitor_keywords(all_competitor_keywords)
            print(f"   ✓ Competitor keywords exported to {comp_keywords_file}")
        
        # Export scraped copy analysis
        if scraped_pages:
            copy_file = csv_exporter.export_scraped_copy(scraped_pages)
            print(f"   ✓ Scraped copy exported to {copy_file}")
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"COMPETITION ANALYSIS SUMMARY")
        print(f"{'='*60}")
        
        summary = analysis.get_competitor_summary()
        print(f"  Competitors Analyzed: {summary['total_competitors']}")
        print(f"  Total Competitor Keywords: {summary['total_competitor_keywords']}")
        print(f"  Keyword Gaps Identified: {summary['total_gaps']}")
        print(f"    - Missing Keywords: {summary['missing_keywords']}")
        print(f"    - Underperforming: {summary['underperforming_keywords']}")
        print(f"    - Opportunities: {summary['opportunity_keywords']}")
        
        if scraped_pages:
            print(f"  Landing Pages Scraped: {summary['pages_scraped']}")
        
        print(f"\n📊 TOP KEYWORD OPPORTUNITIES:")
        print(f"{'='*60}")
        
        for i, gap in enumerate(top_opportunities[:5], 1):
            print(f"{i}. {gap.keyword.term}")
            if gap.keyword.metrics:
                print(f"   Volume: {gap.keyword.metrics.search_volume:,} | "
                     f"CPC: ${gap.keyword.metrics.cpc:.2f} | "
                     f"Competition: {gap.keyword.metrics.competition:.2f}")
            print(f"   {gap.recommendation}")
            print()
        
        print(f"\n💡 KEY RECOMMENDATIONS:")
        print(f"{'='*60}")
        
        for i, rec in enumerate(analysis.recommendations[:5], 1):
            print(f"{i}. {rec}")
        
        print(f"\n✅ Competition analysis complete!")
        print(f"   Results saved to: {output_dir}")
        
        # Save full analysis report as JSON
        import json
        report_file = output_dir / "competition_analysis.json"
        with open(report_file, 'w') as f:
            json.dump(analysis.dict(), f, indent=2, default=str)
        
        print(f"   Full report: {report_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to analyze competition: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1