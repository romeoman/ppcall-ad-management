# DataForSEO CLI - PPC Keyword Research Tool

A command-line interface for DataForSEO API with support for both Google Ads and Bing Ads platforms. This tool enables efficient keyword research, traffic estimation, and audience analysis for PPC campaigns.

## Features

### Platform Support
- **Google Ads**: 6 specialized endpoints for Google Ads campaigns
- **Bing Ads**: 10 comprehensive endpoints for Bing Ads campaigns  
- **Both**: Run the same operation on both platforms for comparison

### Available Endpoints

#### Google Ads Endpoints
1. **search_volume**: Get search volume, CPC, competition, and bid estimates
2. **keywords_for_site**: Extract relevant keywords from competitor websites
3. **keywords_for_keywords**: Generate keyword suggestions from seed keywords
4. **ad_traffic**: Estimate traffic, clicks, impressions, and costs
5. **locations**: Get supported Google Ads locations
6. **languages**: Get supported Google Ads languages

#### Bing Ads Endpoints
1. **search_volume**: Current search volume with device breakdown
2. **search_volume_history**: Historical search trends (12+ months)
3. **keywords_for_site**: Extract keywords for websites on Bing
4. **keywords_for_keywords**: Generate Bing-specific suggestions
5. **keyword_performance**: Device-specific CTR and performance metrics
6. **keyword_suggestions_url**: AI-powered suggestions from landing pages
7. **audience_estimation**: Demographics and audience size estimates
8. **locations**: Supported Bing locations
9. **languages**: Supported Bing languages

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your DataForSEO credentials
```

## Usage Examples

### Basic Search Volume Query

#### Google Ads only:
```bash
python cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=search_volume \
    --keywords="marketing software,email marketing,crm software" \
    --location=2840 \
    --language=en
```

#### Bing Ads only:
```bash
python cli_dataforseo.py keywords \
    --platform=bing \
    --endpoint=search_volume \
    --keywords="marketing software,email marketing" \
    --device=desktop
```

#### Both platforms (comparison):
```bash
python cli_dataforseo.py keywords \
    --platform=both \
    --endpoint=search_volume \
    --keywords="insurance quotes,auto insurance" \
    --output=json
```

### Competitor Analysis

Extract keywords from competitor website:
```bash
python cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=keywords_for_site \
    --url="competitor.com" \
    --exclude-brands \
    --limit=200
```

### Keyword Suggestions

Generate suggestions from seed keywords:
```bash
python cli_dataforseo.py keywords \
    --platform=both \
    --endpoint=keywords_for_keywords \
    --keywords="plumbing,plumber" \
    --limit=100 \
    --sort-by=search_volume
```

### Traffic Estimation

Estimate ad traffic and costs:
```bash
python cli_dataforseo.py keywords \
    --platform=google \
    --endpoint=ad_traffic \
    --keywords="lawyer,attorney,legal services" \
    --bid=25.0 \
    --match=exact \
    --location=2840
```

### Audience Estimation (Bing)

Get audience demographics:
```bash
python cli_dataforseo.py keywords \
    --platform=bing \
    --endpoint=audience_estimation \
    --keywords="fitness,gym,workout" \
    --bid=5.0 \
    --match=broad
```

### Bulk Processing from CSV

Process keywords from a CSV file:
```bash
python cli_dataforseo.py keywords \
    --platform=both \
    --endpoint=search_volume \
    --keywords-file="keywords.csv" \
    --output=csv \
    --output-file="results.csv"
```

### AI-Powered Suggestions (Bing)

Get AI-generated keywords from landing page:
```bash
python cli_dataforseo.py keywords \
    --platform=bing \
    --endpoint=keyword_suggestions_url \
    --url="https://example.com/landing-page" \
    --exclude-brands \
    --limit=50
```

## Command Line Options

### Required Arguments
- `--platform`: Choose `google`, `bing`, or `both`
- `--endpoint`: Select the API endpoint to use
- Input source (one of):
  - `--keywords`: Comma-separated keywords
  - `--keywords-file`: CSV file with keywords
  - `--url`: Website URL (for site-based endpoints)

### Optional Parameters
- `--location`: Location code (default: 2840 for USA)
- `--language`: Language code (default: en)
- `--bid`: Max CPC bid for estimates
- `--match`: Match type (exact, phrase, broad)
- `--limit`: Maximum results (default: 100)
- `--sort-by`: Sort by metric (search_volume, cpc, competition)
- `--date-from`: Start date (YYYY-MM-DD)
- `--date-to`: End date (YYYY-MM-DD)
- `--device`: Device type - desktop, mobile, tablet (Bing only)
- `--exclude-brands`: Exclude branded keywords
- `--output`: Output format (table, json, csv)
- `--output-file`: Save results to file
- `--verbose`: Show all available metrics

## Output Formats

### Table (default)
Human-readable table format in terminal:
```
Google Ads Results:
--------------------------------------------------------------------------------
keyword          | search_volume   | competition     | cpc             
--------------------------------------------------------------------------------
marketing softwa | 14800           | 0.75            | 12.45           
email marketing  | 33100           | 0.68            | 8.50            
```

### JSON
Structured JSON output for programmatic use:
```json
{
  "google": {
    "success": true,
    "data": [
      {
        "keyword": "marketing software",
        "search_volume": 14800,
        "competition": 0.75,
        "cpc": 12.45
      }
    ],
    "cost": 0.005
  }
}
```

### CSV
Spreadsheet-compatible format with platform column:
```csv
keyword,search_volume,competition,cpc,platform
marketing software,14800,0.75,12.45,Google Ads
marketing software,12000,0.70,10.50,Bing Ads
```

## CSV Input Format

For `--keywords-file`, use either format:

### With header:
```csv
keyword
marketing software
email marketing
crm software
```

### Simple list:
```
marketing software
email marketing
crm software
```

## Validate Credentials

Check if your API credentials are valid:
```bash
python cli_dataforseo.py validate --platform=both
```

Output:
```
Credentials Validation:
----------------------------------------
Google     : ✓ Valid
Bing       : ✓ Valid
```

## Rate Limits

- **Google Ads**: 12 requests per minute
- **Bing Ads**: 20 requests per minute
- The CLI respects these limits automatically

## Documentation Links

### Google Ads API
- Overview: https://dataforseo.com/apis/google-ads-api
- Search Volume: https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/
- Keywords for Site: https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/live/
- Keywords for Keywords: https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/live/
- Ad Traffic: https://docs.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/live/

### Bing Ads API
- Overview: https://dataforseo.com/apis/bing-ads-api
- Search Volume: https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/live/
- Keyword Performance: https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/live/
- Audience Estimation: https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/live/
- AI Suggestions: https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/live/

## Error Handling

The CLI provides clear error messages:
- Missing credentials: Check `.env` file
- Invalid endpoint for platform: Use correct platform-endpoint combination
- API errors: Shows status code and message
- Rate limiting: Automatic retry with exponential backoff

## Tips

1. **Start with small batches**: Test with a few keywords before processing large lists
2. **Use both platforms**: Compare metrics between Google and Bing for comprehensive analysis
3. **Save results**: Use `--output-file` to save data for later analysis
4. **Monitor costs**: Check the cost field in results to track API usage
5. **Use appropriate endpoints**: 
   - Site analysis for competitors
   - Suggestions for keyword expansion
   - Traffic estimation for budget planning
   - Audience estimation for targeting