# PPCall Ad Management System

A comprehensive Google Ads campaign management system for phone-based service businesses, focusing on keyword research, ad group organization, and competitive analysis.

## Overview

This tool automates the creation and management of Google Ads campaigns for businesses that operate via phone calls (plumbers, electricians, AC repair, etc.). It handles keyword expansion, categorization, negative keyword generation, and competitive analysis.

## Features

- **Keyword Research & Expansion**: Expand seed keywords using DataforSEO and Serper APIs
- **Smart Categorization**: Automatically organize keywords by service and location
- **Negative Keywords**: Generate and manage negative keywords to prevent wasted ad spend
- **Competitive Analysis**: Process SpyFu CSV exports to identify opportunities
- **Landing Page Insights**: Scrape competitor landing pages using Firecrawl
- **Project Management**: Isolated project folders for campaign reusability
- **CSV Export**: Generate Google Ads-ready CSV files

## Installation

### Prerequisites

- Python 3.8 or higher
- Git

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd "Ad Management"
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv_linux
source venv_linux/bin/activate  # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure API keys:
```bash
cp .env.example .env
# Edit .env and add your API credentials:
# - DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD
# - SERPER_API_KEY
# - FIRECRAWL_API_KEY
```

## Project Structure

```
Ad Management/
├── src/                    # Source code
│   ├── api/               # API integrations
│   ├── core/              # Core business logic
│   ├── input_parser/      # Input parsing and validation
│   ├── models/            # Pydantic data models
│   ├── output_generator/  # CSV and report generation
│   ├── processors/        # Data processing modules
│   └── utils/             # Utility functions
├── projects/              # Campaign projects
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation
├── examples/              # Example files
└── requirements.txt       # Python dependencies
```

## Usage

### CLI Commands (Coming Soon)

```bash
# Create new campaign project
ppcall create --project "plumber-miami" --seed-keywords "plumber,plumbing"

# Research keywords
ppcall research --project "plumber-miami" --categories "emergency,repair,installation"

# Generate ad groups
ppcall generate --project "plumber-miami" --locations "Miami,Miami Beach,Coral Gables"

# Analyze competition
ppcall analyze --project "plumber-miami" --spyfu "competitors.csv"

# Export campaign
ppcall export --project "plumber-miami" --format csv

# Clone project for new market
ppcall clone --source "plumber-miami" --target "plumber-orlando" --location "Orlando"
```

### Project Workflow

1. **Create Project**: Initialize a new campaign project folder
2. **Add Inputs**: Seed keywords, categories, locations, competitor data
3. **Research**: Expand keywords and gather search volume data
4. **Organize**: Create ad groups based on service/location combinations
5. **Analyze**: Review competition and identify opportunities
6. **Export**: Generate CSV files for Google Ads import

## API Configuration

### DataforSEO
- Used for keyword expansion and search volume data
- Requires login and password
- [Sign up here](https://dataforseo.com/)

### Serper
- Alternative/supplementary keyword research
- Requires API key
- [Get API key](https://serper.dev/)

### Firecrawl
- Web scraping for competitor landing pages
- Requires API key
- [Get API key](https://firecrawl.dev/)

## Development

### Running Tests

```bash
# Activate virtual environment
source venv_linux/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Contributing

1. Create a feature branch
2. Make changes with tests
3. Ensure all tests pass
4. Submit pull request

## License

[License information here]

## Support

For issues or questions, please create an issue in the repository.