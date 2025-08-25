### 1. Executive Brief

This executive brief summarizes the Python application for automating PPC keyword research and campaign setup in the home services sector (e.g., plumbing). The app will connect to Data4SEO and SERP APIs to fetch keyword data, expand seed keywords, generate CSVs for organized keywords, negative keywords, and ad groups. It targets affiliates running Google Ads campaigns, focusing on categories like emergency plumbing, water cleanup, and toilet repairs, combined with cities and zip codes. Additional features include competition analysis from SpyFu CSVs and landing page scraping via FireCrawl API for copy insights. The goal is efficiency: rapid research and organization without a UI, enabling quick campaign launches with tracking via ClickFlare and Ringba (handled separately). Expected outcomes: Reduced manual effort, better-targeted ads, and improved ROI through data-driven decisions.

Key Benefits:
- Automates keyword expansion and categorization for scalability.
- Integrates competition data to identify gaps and opportunities.
- Outputs ready-to-use CSVs for Google Ads import.
- Ensures compliance with negative keywords to minimize wasted spend.

Risks and Assumptions:
- API costs and rate limits from Data4SEO, SERP, and FireCrawl must be managed.
- Assumes user provides API keys, seed keywords, cities/zip codes, and SpyFu CSVs.
- No real-time bidding; focuses on pre-campaign setup.

### 2. Product Requirements Document (PRD)

The PRD outlines the functional and non-functional requirements for the Python application. It is structured into sections for clarity, focusing on a command-line tool that processes inputs and generates outputs without a graphical interface.

#### Overview
- **Product Name**: PPC Keyword Automator
- **Version**: 1.0
- **Target Users**: Affiliates in home services PPC campaigns.
- **Problem Solved**: Manual keyword research is time-consuming; this app automates expansion, organization, and export for Google Ads.
- **Success Metrics**: Generate CSVs in under 5 minutes per run; support 100+ keywords/categories; integrate competition data accurately.

#### Functional Requirements
- **Keyword Research and Expansion**:
  - Input: Seed keywords (e.g., "plumbing"), categories (e.g., "emergency plumbing", "toilet repairs"), cities, zip codes.
  - Connect to Data4SEO/SERP APIs to fetch search volume, competition, CPC estimates.
  - Expand keywords (e.g., suggest "emergency plumber near me" based on seeds).
  - Output: Categorized keywords in CSVs (e.g., one sheet per category).
- **Negative Keywords Generation**:
  - Auto-generate negatives (e.g., "free", "DIY" for paid services).
  - Allow user input for custom negatives.
  - Integrate with keyword lists to avoid overlaps.
- **Ad Group Organization**:
  - Combine services with locations (e.g., "emergency plumbing + City A", "toilet repairs + ZIP 12345").
  - Create ad groups: One per combination type (e.g., service-city, service-zip).
  - Export as CSV with columns: Ad Group Name, Keywords, Match Type (broad, phrase, exact).
- **Competition Analysis**:
  - Input: CSV from SpyFu (keywords, ads, competitors).
  - Analyze for overlaps/gaps; suggest additions to user's keyword list.
  - Output: Report CSV with competitor keywords, estimated traffic, and recommendations.
- **Landing Page Scraping**:
  - Input: Competitor URLs from SpyFu or manual list.
  - Use FireCrawl API to scrape copy (headlines, CTAs, body text).
  - Output: CSV with scraped data for inspiration (e.g., "Headline: Fast Plumbing Services").
- **Data Export**:
  - All outputs as CSVs: Keywords, negatives, ad groups, competition insights, scraped copy.
  - Configurable via command-line args (e.g., python app.py --seeds seeds.txt --cities cities.csv).

#### Non-Functional Requirements
- **Performance**: Handle 500+ keywords per run; API calls batched to avoid limits.
- **Security**: Store API keys in environment variables; no hardcoding.
- **Usability**: Command-line interface with help flags; logging for errors.
- **Scalability**: Modular for adding more APIs/categories.
- **Dependencies**: Python 3.10+; use Pydantic for data validation.

#### User Stories
- As an affiliate, I want to input seed keywords and locations so the app generates expanded lists.
- As a user, I want to upload SpyFu CSVs to compare against my keywords.
- As a campaign manager, I want auto-generated ad groups and negatives for quick Google Ads import.

#### Out of Scope
- UI development; real-time tracking (use ClickFlare/Ringba separately); actual ad uploading to Google Ads.

### 3. Solution Architecture

The architecture is a modular, script-based Python application running locally or in a cloud environment (e.g., via Cursor IDE). It follows a pipeline approach: Input → Processing → API Integration → Output.

- **High-Level Components**:
  - **Input Layer**: Command-line parser (argparse) for seeds, cities, zips, SpyFu CSVs, URLs.
  - **Data Modeling Layer**: Pydantic models for validation (e.g., KeywordSchema with fields like term, volume, category).
  - **Core Logic Layer**: Modules for keyword expansion, combination generation, negative keyword creation, competition analysis.
  - **API Integration Layer**: Connectors for Data4SEO, SERP, FireCrawl (using requests or SDKs).
  - **Output Layer**: CSV writers (pandas) for exports; logging for debugging.
- **Data Flow**:
  1. Parse inputs → Validate with Pydantic.
  2. Fetch/expand keywords via APIs.
  3. Process combinations and analyses.
  4. Generate CSVs.
- **Error Handling**: Retry on API failures; graceful exits on invalid inputs.
- **Deployment**: Standalone script; run via CLI. For scaling, containerize with Docker.

Visual Representation:

| Layer | Components | Technologies |
|-------|------------|--------------|
| Input | CLI Parser, File Readers | argparse, pandas |
| Data | Models, Validation | Pydantic |
| Processing | Expansion, Combinations, Analysis | Custom Python functions, pandas for data manipulation |
| Integration | API Calls | requests library, API SDKs if available |
| Output | CSV Generators, Logs | pandas, logging module |

### 4. Data Sets

The app relies on user-provided and API-fetched data sets. All are handled as CSVs or text files for simplicity.

- **Input Data Sets**:
  - Seed Keywords: TXT or CSV file (e.g., columns: Keyword, Category). Example: "plumbing, general"; "emergency plumbing, urgent".
  - Categories: List in CSV (e.g., "emergency plumbing", "water cleanup", "toilet repairs").
  - Locations: CSV with cities and zip codes (e.g., columns: City, Zip). Example: "New York, 10001"; "Los Angeles, 90001".
  - SpyFu Competition Data: CSV export (columns: Competitor Keyword, Volume, CPC, Ad Copy).
  - Competitor URLs: TXT list for scraping.

- **Fetched/Generated Data Sets**:
  - Keyword Metrics: From Data4SEO/SERP (e.g., search volume, competition score, suggested keywords).
  - Scraped Landing Pages: From FireCrawl (e.g., headlines, paragraphs, CTAs).
  - Expanded Keywords: Generated lists (e.g., "emergency plumber in New York").
  - Negative Keywords: Auto-generated (e.g., "cheap", "free") + user customs.
  - Ad Groups: Combined outputs (e.g., "Emergency Plumbing - NYC" with associated keywords).

- **Output Data Sets**:
  - Keywords CSV: Columns - Keyword, Category, Volume, CPC, Location.
  - Negatives CSV: Columns - Negative Keyword, Reason.
  - Ad Groups CSV: Columns - Ad Group Name, Keywords (list), Match Type.
  - Competition Report CSV: Columns - Competitor Keyword, Overlap (yes/no), Recommendation.
  - Scraped Copy CSV: Columns - URL, Headline, Body Snippet.

Data Volume: Start small (100-500 rows); scale as needed. Use pandas for manipulation to ensure cleanliness.

### 5. Tech Stack

The tech stack emphasizes Python for core development, with libraries for efficiency. Development in Cursor IDE; coding assistance via Claude Opus.

- **Core Language**: Python 3.10+ (for type hints and performance).
- **Data Validation**: Pydantic (for modeling schemas like Keyword, AdGroup).
- **API Integration**:
  - Data4SEO and SERP: requests library or official Python SDKs.
  - FireCrawl: Official Python client for scraping.
- **Data Processing**: pandas (for CSV handling, data frames); numpy (if needed for calculations).
- **Command-Line Interface**: argparse (for inputs/flags).
- **Logging and Error Handling**: logging module; tenacity for API retries.
- **Environment Management**: dotenv for API keys; virtualenv or poetry for dependencies.
- **Testing**: pytest (unit tests for modules).
- **Optional Extensions**: If needed, add asyncio for parallel API calls.

Installation Example (via requirements.txt):
```
pydantic
pandas
requests
python-dotenv
tenacity
argparse  # Built-in, but for clarity
```