# PPC Campaign Manager - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [CLI Command Reference](#cli-command-reference)
3. [Project Setup](#project-setup)
4. [Keyword Research](#keyword-research)
5. [Competition Analysis](#competition-analysis)
6. [Campaign Generation](#campaign-generation)
7. [Workflow Examples](#workflow-examples)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## CLI Command Reference

### Main PPC CLI (`ppc.py`)

The main CLI provides commands for managing PPC campaigns end-to-end.

#### Global Options
```bash
--verbose, -v    # Enable verbose output for debugging
--quiet, -q      # Suppress non-error output
--help, -h       # Show help for any command
```

#### Available Commands

##### `create` - Create New Project
```bash
python ppc.py create PROJECT_NAME [options]

Options:
  --template TEMPLATE        # Use existing project as template
  --industry {plumbing,hvac,electrical,roofing,general}
  --platforms {google,bing,both}
  --interactive             # Interactive configuration mode

Examples:
  python ppc.py create plumber-miami
  python ppc.py create hvac-orlando --industry hvac
  python ppc.py create locksmith-tampa --template plumber-miami
```

##### `research` - Keyword Research & Expansion
```bash
python ppc.py research --project PROJECT [options]

Required:
  --project, -p PROJECT     # Project name or path

Options:
  --seeds FILE             # Custom seed keywords file
  --depth {1,2,3}         # Expansion depth (default: 2)
  --locations FILE        # Custom locations file
  --min-volume NUMBER     # Minimum search volume (default: 10)
  --max-cpc AMOUNT        # Maximum CPC filter (default: 50.0)
  --platform {google,bing,both}

Examples:
  python ppc.py research --project plumber-miami
  python ppc.py research -p plumber-miami --min-volume 100 --max-cpc 25
  python ppc.py research -p plumber-miami --depth 3 --platform google
```

##### `generate` - Generate Ad Groups
```bash
python ppc.py generate --project PROJECT [options]

Required:
  --project, -p PROJECT     # Project name or path

Options:
  --match-types {broad,phrase,exact}  # Match types (default: all)
  --group-by {service,location,both}  # Grouping strategy
  --max-keywords-per-group NUMBER      # Max keywords per group (default: 20)
  --include-negatives                  # Generate negative keywords

Examples:
  python ppc.py generate --project plumber-miami
  python ppc.py generate -p plumber-miami --match-types exact
  python ppc.py generate -p plumber-miami --group-by location --include-negatives
```

##### `analyze` - Competition Analysis
```bash
python ppc.py analyze --project PROJECT [options]

Required:
  --project, -p PROJECT     # Project name or path

Options:
  --competitors URL [URL...] # Competitor URLs to analyze
  --spyfu FILE              # SpyFu export CSV file
  --scrape-landing-pages    # Scrape competitor landing pages
  --identify-gaps           # Find keyword opportunities

Examples:
  python ppc.py analyze --project plumber-miami --scrape-landing-pages
  python ppc.py analyze -p plumber-miami --competitors competitor1.com competitor2.com
  python ppc.py analyze -p plumber-miami --spyfu spyfu_export.csv --identify-gaps
```

##### `export` - Export Campaigns
```bash
python ppc.py export --project PROJECT [options]

Required:
  --project, -p PROJECT     # Project name or path

Options:
  --format {google,bing,csv,all}  # Export format (default: all)
  --output DIR                     # Output directory
  --include-settings              # Include campaign settings
  --zip                          # Create ZIP archive

Examples:
  python ppc.py export --project plumber-miami
  python ppc.py export -p plumber-miami --format google --zip
  python ppc.py export -p plumber-miami --output ~/exports --include-settings
```

##### `list` - List Projects
```bash
python ppc.py list [options]

Options:
  --detailed, -d           # Show detailed information
  --filter {active,archived,all}  # Filter by status

Examples:
  python ppc.py list
  python ppc.py list --detailed
  python ppc.py list --filter all -d
```

##### `clone` - Clone Project
```bash
python ppc.py clone SOURCE TARGET [options]

Arguments:
  SOURCE                   # Source project to clone
  TARGET                   # New project name

Options:
  --clear-outputs         # Clear output files (default: true)
  --clear-cache          # Clear API cache (default: true)

Examples:
  python ppc.py clone plumber-miami plumber-orlando
  python ppc.py clone plumber-miami plumber-tampa --clear-cache
```

### DataForSEO CLI (`cli_dataforseo.py`)

Direct access to DataForSEO API endpoints for advanced users.

#### Command Structure
```bash
python cli_dataforseo.py keywords --platform PLATFORM --endpoint ENDPOINT [options]
```

#### Common Options
```bash
--platform {google,bing,both}   # Target platform
--endpoint ENDPOINT              # API endpoint to use
--location CODE                  # Location code (default: 2840 for USA)
--language CODE                  # Language code (default: en)
--output {table,json,csv}       # Output format
--output-file FILE              # Save to file
--verbose                       # Show all metrics
```

#### Google Ads Endpoints

##### `search_volume` - Get Search Volume Data
```bash
python cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=search_volume \
    --keywords="keyword1,keyword2" \
    --location=2840

# From file
python cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=search_volume \
    --keywords-file="keywords.csv"
```

##### `keywords_for_site` - Extract Keywords from Website
```bash
python cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=keywords_for_site \
    --url="example.com" \
    --limit=500 \
    --exclude-brands
```

##### `keywords_for_keywords` - Generate Keyword Suggestions
```bash
python cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=keywords_for_keywords \
    --keywords="seed1,seed2" \
    --limit=100 \
    --sort-by=search_volume
```

##### `ad_traffic` - Estimate Ad Traffic
```bash
python cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=ad_traffic \
    --keywords="keyword1,keyword2" \
    --bid=25.0 \
    --match=exact \
    --location=2840
```

#### Bing Ads Endpoints

##### `search_volume` - Current Search Volume
```bash
python cli_dataforseo.py keywords \
    --platform=bing \
    --endpoint=search_volume \
    --keywords="keyword1,keyword2" \
    --device=desktop
```

##### `search_volume_history` - Historical Trends
```bash
python cli_dataforseo.py keywords \
    --platform=bing \
    --endpoint=search_volume_history \
    --keywords="keyword1,keyword2" \
    --date-from="2024-01-01" \
    --date-to="2024-12-31"
```

##### `keyword_performance` - Performance Metrics
```bash
python cli_dataforseo.py keywords \
    --platform=bing \
    --endpoint=keyword_performance \
    --keywords="keyword1,keyword2" \
    --match=exact
```

##### `audience_estimation` - Demographics Data
```bash
python cli_dataforseo.py keywords \
    --platform=bing \
    --endpoint=audience_estimation \
    --keywords="keyword1,keyword2" \
    --bid=5.0
```

#### Comparing Platforms
```bash
# Get data from both Google and Bing
python cli_dataforseo.py keywords \
    --platform=both \
    --endpoint=search_volume \
    --keywords="plumber miami,emergency plumber" \
    --output=csv \
    --output-file="comparison.csv"
```

#### Validation and Status
```bash
# Validate API credentials
python cli_dataforseo.py validate --platform=both

# Check API status and limits
python cli_dataforseo.py status
```

## Getting Started

### Prerequisites
Before using the PPC Campaign Manager, ensure you have:
- Python 3.8+ installed
- API credentials for DataForSEO (required)
- API credentials for FireCrawl (optional, for landing page analysis)
- SpyFu export CSV (optional, for competitor data)

### Initial Setup

1. **Activate the virtual environment:**
```bash
cd "Ad Management"
source venv_linux/bin/activate
```

2. **Configure your API credentials:**
```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

Add your credentials:
```env
DATAFORSEO_LOGIN=your_login
DATAFORSEO_PASSWORD=your_password
FIRECRAWL_API_KEY=your_api_key  # Optional
```

3. **Verify installation:**
```bash
python ppc.py --help
```

## Project Setup

### Creating a New Campaign Project

1. **Initialize a new project:**
```bash
python ppc.py create --project "plumber-miami"
```

This creates a project structure:
```
projects/plumber-miami/
├── inputs/
│   ├── keywords/
│   │   └── seed_keywords.txt
│   ├── locations/
│   │   └── cities.csv
│   ├── competitors/
│   │   ├── competitor_urls.txt
│   │   └── spyfu_export.csv
│   └── negative_keywords/
│       └── negative_keywords.txt
├── outputs/
│   ├── keywords/
│   ├── ad_groups/
│   └── competition/
└── .cache/
```

2. **Add seed keywords:**
Create or edit `projects/plumber-miami/inputs/keywords/seed_keywords.txt`:
```
plumber
plumbing repair
emergency plumber
water heater installation
drain cleaning
```

3. **Add target locations:**
Create `projects/plumber-miami/inputs/locations/cities.csv`:
```csv
City,State,Zip
Miami,FL,33101
Miami Beach,FL,33139
Coral Gables,FL,33134
Homestead,FL,33030
```

## Keyword Research

### Expanding Keywords

1. **Basic keyword expansion:**
```bash
python ppc.py research --project "plumber-miami"
```

2. **With specific parameters:**
```bash
python ppc.py research \
    --project "plumber-miami" \
    --min-volume 100 \
    --max-cpc 50 \
    --depth 2
```

3. **Using both Google and Bing data:**
```bash
python cli_dataforseo.py keywords \
    --platform=both \
    --endpoint=keywords_for_keywords \
    --keywords-file="projects/plumber-miami/inputs/keywords/seed_keywords.txt" \
    --output-file="projects/plumber-miami/outputs/keywords/expanded_keywords.csv"
```

### Understanding the Output

The research command generates:
- `expanded_keywords_[timestamp].csv` - All expanded keywords with metrics
- Columns include: Keyword, Category, Volume, CPC, Competition, Location

## Competition Analysis

### Analyzing Competitor Websites

1. **Add competitor URLs:**
Create `projects/plumber-miami/inputs/competitors/competitor_urls.txt`:
```
https://www.competitor1.com
https://www.competitor2.com
https://www.competitor3.com
```

2. **Run competition analysis:**
```bash
python ppc.py analyze \
    --project "plumber-miami" \
    --scrape-pages \
    --our-domain "yoursite.com"
```

### Processing SpyFu Data

1. **Export data from SpyFu:**
   - Log into SpyFu
   - Search for competitor domains
   - Export keyword data as CSV

2. **Place in project folder:**
```bash
cp ~/Downloads/spyfu_export.csv projects/plumber-miami/inputs/competitors/
```

3. **Run analysis with SpyFu data:**
```bash
python ppc.py analyze \
    --project "plumber-miami" \
    --spyfu "projects/plumber-miami/inputs/competitors/spyfu_export.csv"
```

### Analysis Output

The analyze command generates:
- `keyword_gaps_[timestamp].csv` - Keywords competitors rank for that you don't
- `competitor_keywords_[timestamp].csv` - All competitor keywords with metrics
- `scraped_copy_[timestamp].csv` - Landing page copy analysis
- `competition_analysis.json` - Complete analysis report

## Campaign Generation

### Creating Ad Groups

1. **Generate ad groups from keywords:**
```bash
python ppc.py generate \
    --project "plumber-miami" \
    --match-type exact \
    --group-size 20
```

2. **With location-based campaigns:**
```bash
python ppc.py generate \
    --project "plumber-miami" \
    --locations "projects/plumber-miami/inputs/locations/cities.csv" \
    --location-strategy separate
```

### Managing Negative Keywords

1. **Generate negative keywords automatically:**
```bash
python ppc.py negatives \
    --project "plumber-miami" \
    --auto-generate
```

2. **Add custom negative keywords:**
Edit `projects/plumber-miami/inputs/negative_keywords/negative_keywords.txt`:
```
free
diy
tutorial
how to
cheap
```

### Exporting for Google Ads

1. **Export campaign structure:**
```bash
python ppc.py export \
    --project "plumber-miami" \
    --format google-ads \
    --campaign-name "Miami Plumbing Services"
```

2. **Export with all components:**
```bash
python ppc.py export \
    --project "plumber-miami" \
    --include-negatives \
    --include-extensions \
    --format csv
```

## Workflow Examples

### Complete Campaign Setup Workflow

```bash
# 1. Create project
python ppc.py create --project "plumber-miami"

# 2. Add seed keywords and locations (manually edit files)

# 3. Research keywords
python ppc.py research --project "plumber-miami" --min-volume 100

# 4. Analyze competition
python ppc.py analyze --project "plumber-miami" --scrape-pages

# 5. Generate negative keywords
python ppc.py negatives --project "plumber-miami" --auto-generate

# 6. Create ad groups
python ppc.py generate --project "plumber-miami" --match-type exact

# 7. Export for Google Ads
python ppc.py export --project "plumber-miami" --format google-ads
```

### Cloning Project for New Market

```bash
# Clone Miami campaign for Orlando
python ppc.py clone \
    --source "plumber-miami" \
    --target "plumber-orlando" \
    --new-location "Orlando,FL"

# Update location-specific keywords
python ppc.py research \
    --project "plumber-orlando" \
    --locations "Orlando,Winter Park,Kissimmee"
```

### Using DataForSEO CLI Directly

```bash
# Get search volume for specific keywords
python cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=search_volume \
    --keywords="emergency plumber miami,24 hour plumber miami" \
    --location=2840

# Analyze competitor website
python cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=keywords_for_site \
    --url="competitor.com" \
    --limit=500 \
    --output-file="competitor_keywords.csv"

# Estimate traffic for keywords
python cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=ad_traffic \
    --keywords-file="projects/plumber-miami/outputs/keywords/final_keywords.csv" \
    --bid=25.0 \
    --match=exact
```

## Best Practices

### Keyword Research
1. **Start with broad seed keywords** - Let the API expand them
2. **Use category-specific seeds** - "emergency", "repair", "installation"
3. **Set reasonable filters** - Min volume: 50-100, Max CPC: based on budget
4. **Review expanded keywords** - Remove irrelevant terms before generating ad groups

### Competition Analysis
1. **Analyze 3-5 top competitors** - Focus on direct competition
2. **Look for keyword gaps** - High-volume keywords you're missing
3. **Study landing page copy** - Identify common CTAs and value props
4. **Monitor regularly** - Run monthly competitive analysis

### Ad Group Organization
1. **Keep groups tight** - 15-25 closely related keywords
2. **Match intent** - Don't mix informational and transactional
3. **Separate by location** - City-specific campaigns perform better
4. **Use SKAG for high-value** - Single Keyword Ad Groups for top terms

### Negative Keywords
1. **Start with universal negatives** - free, cheap, diy, tutorial
2. **Add industry-specific** - Based on your service limitations
3. **Review search terms regularly** - Add new negatives from actual data
4. **Use match types** - Broad match for common negatives

## Troubleshooting

### Common Issues

**API Rate Limits:**
```
Error: Rate limit exceeded
```
Solution: Add delays between requests or upgrade API plan

**Missing Keywords File:**
```
FileNotFoundError: seed_keywords.txt not found
```
Solution: Ensure file exists in `projects/[name]/inputs/keywords/`

**Invalid API Credentials:**
```
Error: Authentication failed
```
Solution: Check `.env` file for correct credentials

**Empty Results:**
```
No keywords found after filtering
```
Solution: Adjust filter parameters (lower min_volume, higher max_cpc)

### Debug Mode

Run commands with verbose output:
```bash
python ppc.py research --project "plumber-miami" --verbose --debug
```

### Checking API Status

Validate credentials:
```bash
python cli_dataforseo.py validate --platform=both
```

Check API limits:
```bash
python cli_dataforseo.py status
```

## Advanced Features

### Custom Processing

1. **Process specific competitor data:**
```python
from src.processors.competition_analyzer import CompetitionAnalyzer
from api_integration.dataforseo.google_ads_client import GoogleAdsClient

client = GoogleAdsClient(login, password)
analyzer = CompetitionAnalyzer(client)

# Analyze specific competitor
competitor = await analyzer.analyze_competitor_website(
    "https://competitor.com",
    location_code=2840,
    limit=1000
)
```

2. **Bulk keyword processing:**
```python
from src.processors.keyword_processor import KeywordProcessor

processor = KeywordProcessor(google_ads_client)
expanded = processor.expand_seed_keywords(
    seed_keywords,
    platform="google_ads",
    include_seed_in_results=True
)
```

### Export Formats

1. **Google Ads Editor format:**
```bash
python ppc.py export --project "plumber-miami" --format google-ads-editor
```

2. **Bing Ads format:**
```bash
python ppc.py export --project "plumber-miami" --format bing-ads
```

3. **Custom CSV with specific fields:**
```bash
python ppc.py export \
    --project "plumber-miami" \
    --format csv \
    --fields "keyword,volume,cpc,ad_group"
```

## Support

For issues or questions:
1. Check the [README](README.md) for setup instructions
2. Review error messages in `logs/` directory
3. Create an issue in the repository with:
   - Error message
   - Command used
   - Expected vs actual behavior

## Next Steps

1. **Monitor Performance** - Track CTR, CPC, and conversions
2. **A/B Test Ad Copy** - Use landing page insights for ideas
3. **Expand Successful Keywords** - Use top performers as new seeds
4. **Refine Negatives** - Based on actual search terms
5. **Scale to New Markets** - Clone successful campaigns

## CLI Quick Reference Card

### Most Common Commands

```bash
# Project Management
ppc.py create PROJECT_NAME           # Create new project
ppc.py list                         # List all projects
ppc.py clone SOURCE TARGET          # Clone project

# Campaign Workflow
ppc.py research -p PROJECT          # Expand keywords
ppc.py analyze -p PROJECT           # Analyze competition
ppc.py generate -p PROJECT          # Create ad groups
ppc.py export -p PROJECT            # Export campaigns

# DataForSEO Direct Access
cli_dataforseo.py validate --platform=both     # Check credentials
cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=search_volume \
    --keywords-file="keywords.csv"             # Get search volumes

cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=keywords_for_site \
    --url="competitor.com"                     # Analyze competitor
```

### Command Shortcuts

| Command | Short | Description |
|---------|-------|-------------|
| `--project` | `-p` | Specify project |
| `--verbose` | `-v` | Debug output |
| `--quiet` | `-q` | Minimal output |
| `--help` | `-h` | Show help |
| `--output` | `-o` | Output path |
| `--format` | `-f` | Export format |
| `--detailed` | `-d` | Detailed view |

### Platform Codes

| Platform | Location Code | Description |
|----------|--------------|-------------|
| Google | 2840 | United States |
| Google | 1006094 | Miami, FL |
| Google | 1006095 | Orlando, FL |
| Google | 1006096 | Tampa, FL |
| Bing | 190 | United States |

### Match Types

| Symbol | Type | Example |
|--------|------|---------|
| (none) | Broad | `plumber miami` |
| `" "` | Phrase | `"plumber miami"` |
| `[ ]` | Exact | `[plumber miami]` |
| `-` | Negative | `-free` |

### File Locations

```
projects/PROJECT_NAME/
├── inputs/
│   ├── keywords/seed_keywords.txt
│   ├── locations/cities.csv
│   ├── competitors/competitor_urls.txt
│   └── negative_keywords/negative_keywords.txt
└── outputs/
    ├── keywords/expanded_keywords_*.csv
    ├── ad_groups/ad_groups_*.csv
    └── competition/keyword_gaps_*.csv
```