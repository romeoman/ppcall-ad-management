# PPC Campaign Manager

A production-ready PPC campaign management system for service businesses, automating keyword research, competitive analysis, and campaign generation for Google Ads and Bing Ads.

## 🚀 Overview

PPC Campaign Manager is a comprehensive tool designed for businesses that generate leads through phone calls (plumbers, electricians, HVAC, locksmiths, etc.). It automates the entire PPC campaign creation process from keyword research to export-ready campaign structures.

## ✨ Features

### Core Capabilities
- **🔍 Keyword Research & Expansion**: Leverage DataForSEO's Google Ads and Bing Ads APIs for comprehensive keyword discovery
- **📊 Competitive Analysis**: Analyze competitor websites, identify keyword gaps, and discover opportunities
- **📈 SpyFu Integration**: Process SpyFu exports to gain competitive insights
- **🌐 Landing Page Analysis**: Scrape and analyze competitor landing pages with FireCrawl
- **🎯 Smart Ad Group Generation**: Automatically organize keywords into tightly-themed ad groups
- **🚫 Negative Keywords**: AI-powered negative keyword generation to reduce wasted spend
- **📍 Location Targeting**: Create location-specific campaigns with city-level targeting
- **📁 Project Management**: Isolated project folders for multi-client campaign management
- **📤 Export Formats**: Google Ads Editor, Bing Ads, and CSV export formats

### Advanced Features
- **Error Handling**: Robust retry logic with exponential backoff for API reliability
- **Progress Tracking**: Resume interrupted operations from last checkpoint
- **Caching System**: Intelligent caching to reduce API costs and improve speed
- **Batch Processing**: Efficient handling of large keyword lists
- **Multi-Platform Support**: Simultaneous Google Ads and Bing Ads campaign creation

## 📦 Installation

### Prerequisites

- Python 3.8+
- Git
- API credentials (at least DataForSEO is required)

### Quick Start

1. **Clone the repository:**
```bash
git clone <repository-url>
cd "Ad Management"
```

2. **Set up virtual environment:**
```bash
python3 -m venv venv_linux
source venv_linux/bin/activate  # On Linux/Mac
# or
venv_linux\Scripts\activate     # On Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure API credentials:**
```bash
cp .env.example .env
nano .env  # Add your credentials:
```

Required credentials:
```env
# DataForSEO (Required)
DATAFORSEO_LOGIN=your_login
DATAFORSEO_PASSWORD=your_password

# FireCrawl (Optional - for landing page analysis)
FIRECRAWL_API_KEY=your_api_key

# Serper (Optional - alternative keyword source)
SERPER_API_KEY=your_api_key
```

## 📁 Project Structure

```
Ad Management/
├── src/
│   ├── api_integration/       # External API clients
│   │   ├── dataforseo/       # DataForSEO integration
│   │   ├── serper_client.py  # Serper API client
│   │   └── firecrawl_client.py # FireCrawl client
│   ├── cli_commands/         # CLI command implementations
│   ├── input_parser/         # Input file parsers
│   ├── output_generator/     # Export and reporting
│   ├── processors/           # Data processing modules
│   │   ├── keyword_processor.py
│   │   ├── ad_group_processor.py
│   │   ├── competition_analyzer.py
│   │   └── landing_page_scraper.py
│   ├── project_manager/      # Project management
│   └── utils/                # Utilities and helpers
├── models/                   # Pydantic data models
├── projects/                 # Campaign project storage
├── tests/                    # Comprehensive test suite
├── docs/                     # Documentation
├── ppc.py                    # Main CLI entry point
├── cli_dataforseo.py        # DataForSEO CLI tool
└── requirements.txt          # Dependencies
```

## 🎯 Usage

### Available CLIs

The system provides two command-line interfaces:

1. **`ppc.py`** - Main campaign management CLI
2. **`cli_dataforseo.py`** - Direct DataForSEO API access

### Quick Start Example

```bash
# 1. Create a new project
python ppc.py create "plumber-miami"

# 2. Add seed keywords to projects/plumber-miami/inputs/keywords/seed_keywords.txt
echo "plumber\nplumbing repair\nemergency plumber" > projects/plumber-miami/inputs/keywords/seed_keywords.txt

# 3. Research and expand keywords
python ppc.py research --project "plumber-miami" --min-volume 100 --max-cpc 50

# 4. Analyze competition
python ppc.py analyze --project "plumber-miami" --scrape-landing-pages

# 5. Generate ad groups
python ppc.py generate --project "plumber-miami" --match-types exact

# 6. Export for Google Ads
python ppc.py export --project "plumber-miami" --format google
```

### DataForSEO CLI Usage

```bash
# Get search volume for keywords
python cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=search_volume \
    --keywords="plumber miami,emergency plumber" \
    --location=2840

# Analyze competitor website
python cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=keywords_for_site \
    --url="competitor.com" \
    --limit=500

# Compare Google vs Bing
python cli_dataforseo.py keywords \
    --platform=both \
    --endpoint=search_volume \
    --keywords-file="keywords.csv"
```

## 🔧 Key Components

### Keyword Processor
- Expands seed keywords using multiple data sources
- Filters by search volume, CPC, and competition
- Categorizes keywords by service type and intent
- Supports location-based keyword variations

### Competition Analyzer
- Analyzes competitor websites using DataForSEO's Keywords for Site API
- Processes SpyFu CSV exports for historical data
- Identifies keyword gaps and opportunities
- Calculates opportunity scores based on volume and competition

### Ad Group Processor
- Creates tightly-themed ad groups (15-25 keywords)
- Supports multiple match types (broad, phrase, exact)
- Implements SKAG (Single Keyword Ad Groups) for high-value terms
- Location-based campaign splitting

### Landing Page Scraper
- Extracts competitor landing page content
- Identifies CTAs, value propositions, and features
- Analyzes meta tags and structured data
- Provides insights for ad copy creation

## 📊 Competition Analysis Features

The system provides comprehensive competitive intelligence:

1. **Keyword Gap Analysis**
   - Missing keywords (competitors rank, you don't)
   - Underperforming keywords (competitors rank better)
   - Opportunity keywords (high volume, low competition)

2. **Competitor Metrics**
   - Organic vs paid keyword distribution
   - Average positions and rankings
   - Estimated traffic and costs
   - Domain authority indicators

3. **Landing Page Insights**
   - Headlines and value propositions
   - Call-to-action analysis
   - Feature comparisons
   - Pricing strategies

## 🧪 Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_processors/
pytest tests/test_api_integration/

# Run with coverage report
pytest --cov=src --cov-report=html

# Run tests in verbose mode
pytest -v
```

## 📖 Documentation

- **[User Guide](USER_GUIDE.md)** - Complete usage instructions and workflows
- **[DataForSEO CLI Guide](README_DATAFORSEO_CLI.md)** - Detailed API usage examples
- **[API Documentation](docs/api_reference.md)** - Technical API reference

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Format code with Black (`black src/ tests/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📝 License

This project is proprietary software. All rights reserved.

## 💬 Support

For support and questions:
- Create an issue in the repository
- Check the [User Guide](USER_GUIDE.md) for detailed instructions
- Review the [troubleshooting section](USER_GUIDE.md#troubleshooting)

## 🚀 Roadmap

### Upcoming Features
- [ ] Google Ads API direct integration
- [ ] Automated bid management
- [ ] Performance tracking and reporting
- [ ] A/B testing framework
- [ ] Machine learning keyword suggestions
- [ ] Multi-language support
- [ ] Facebook Ads integration
- [ ] Microsoft Ads API integration

## 🙏 Acknowledgments

- DataForSEO for comprehensive keyword data
- FireCrawl for reliable web scraping
- The open-source Python community

---

**Built with ❤️ for PPC professionals**