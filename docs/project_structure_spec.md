# Project Folder Structure Specification

## Overview
This document defines the standardized folder structure for campaign projects in the PPC Keyword Automator. Each project is self-contained in its own folder under the `projects/` directory, enabling easy cloning and recreation of campaigns across different niches.

## Root Project Structure

```
projects/
└── {project_name}/           # e.g., "plumbing_campaign", "electrical_services"
    ├── inputs/               # All input files for the campaign
    ├── configs/              # Configuration files
    ├── outputs/              # Generated output files
    ├── cache/                # Cached API responses for cost optimization
    ├── logs/                 # Project-specific logs
    └── metadata.json         # Project metadata and state

```

## Detailed Folder Structure

### 1. Inputs Directory (`inputs/`)
Stores all user-provided and preprocessed input files.

```
inputs/
├── keywords/
│   ├── seed_keywords.txt           # Initial seed keywords (one per line)
│   ├── seed_keywords.csv           # Alternative CSV format
│   └── negative_keywords.txt       # User-provided negative keywords
├── locations/
│   ├── cities.csv                  # Target cities (name, state)
│   ├── zipcodes.csv               # Target zip codes
│   └── locations_combined.csv     # Processed locations file
├── categories/
│   ├── services.csv               # Service categories
│   ├── categories.txt             # Simple category list
│   └── category_mappings.json     # Category-keyword mappings
├── competitors/
│   ├── competitor_urls.txt        # List of competitor URLs
│   ├── spyfu_export.csv          # SpyFu competition data
│   └── competitor_keywords.csv    # Extracted competitor keywords
└── custom/
    └── {custom_input_files}      # Any additional custom inputs
```

### 2. Configs Directory (`configs/`)
Stores all configuration files for the project.

```
configs/
├── project_config.json            # Main project configuration
├── api_config.json               # API settings and credentials reference
├── campaign_settings.json        # Campaign-specific parameters
├── processing_rules.json         # Keyword processing rules
└── templates/
    ├── ad_group_template.json   # Template for ad group structure
    └── output_format.json       # Output formatting preferences
```

### 3. Outputs Directory (`outputs/`)
Contains all generated files ready for use or import.

```
outputs/
├── keywords/
│   ├── expanded_keywords.csv        # All expanded keywords with metrics
│   ├── categorized_keywords.csv     # Keywords organized by category
│   └── final_keywords.csv          # Final processed keyword list
├── ad_groups/
│   ├── ad_groups_by_location.csv   # Ad groups organized by location
│   ├── ad_groups_by_service.csv    # Ad groups organized by service
│   └── ad_groups_combined.csv      # All ad groups combined
├── negatives/
│   ├── negative_keywords.csv       # Generated negative keywords
│   ├── negative_lists.csv         # Organized negative lists
│   └── shared_negatives.csv       # Shared negative keyword lists
├── analysis/
│   ├── competition_report.csv      # Competition analysis results
│   ├── keyword_gaps.csv           # Identified keyword opportunities
│   ├── landing_page_insights.csv   # Scraped landing page data
│   └── performance_predictions.csv # Performance estimates
├── exports/
│   ├── google_ads_import.csv      # Google Ads formatted export
│   ├── bing_ads_import.csv        # Bing Ads formatted export
│   └── campaign_export.zip        # Complete campaign export package
└── reports/
    ├── campaign_summary.txt        # Human-readable summary
    ├── statistics.json            # Campaign statistics
    └── generation_report.html     # Detailed HTML report
```

### 4. Cache Directory (`cache/`)
Stores cached API responses to reduce costs and improve performance.

```
cache/
├── dataforseo/
│   ├── search_volume/
│   │   └── {hash}_{timestamp}.json
│   ├── keyword_suggestions/
│   │   └── {hash}_{timestamp}.json
│   └── competitor_analysis/
│       └── {hash}_{timestamp}.json
├── serper/
│   └── {cached_responses}.json
└── firecrawl/
    └── {cached_scraped_pages}.json
```

### 5. Logs Directory (`logs/`)
Project-specific logging for debugging and auditing.

```
logs/
├── api_calls.log              # API call history
├── processing.log             # Processing pipeline logs
├── errors.log                 # Error logs
└── audit.log                  # User actions and changes
```

### 6. Project Metadata (`metadata.json`)
Root-level file containing project information.

```json
{
  "project_id": "uuid-here",
  "project_name": "plumbing_campaign",
  "created_date": "2024-08-26T10:00:00Z",
  "last_modified": "2024-08-26T15:30:00Z",
  "version": "1.0.0",
  "parent_project": null,
  "description": "Emergency plumbing services campaign for Dallas area",
  "tags": ["plumbing", "emergency", "dallas"],
  "status": "active",
  "statistics": {
    "total_keywords": 0,
    "total_ad_groups": 0,
    "total_locations": 0,
    "api_calls_made": 0,
    "last_generation_date": null
  },
  "configuration_hash": "sha256_hash_of_configs"
}
```

## Configuration File Schemas

### project_config.json
```json
{
  "project_name": "plumbing_campaign",
  "target_platforms": ["google_ads", "bing_ads"],
  "target_locations": {
    "type": "cities",
    "include_surrounding": true,
    "radius_miles": 25
  },
  "keyword_settings": {
    "match_types": ["exact", "phrase", "broad"],
    "include_variations": true,
    "min_search_volume": 10,
    "max_cpc": 50.00
  },
  "budget_settings": {
    "daily_budget": 500.00,
    "target_cpa": 75.00
  },
  "language": "en",
  "currency": "USD"
}
```

### campaign_settings.json
```json
{
  "campaign_type": "search",
  "bidding_strategy": "maximize_conversions",
  "ad_rotation": "optimize",
  "delivery_method": "standard",
  "networks": {
    "search": true,
    "search_partners": false,
    "display": false
  },
  "scheduling": {
    "start_date": "2024-09-01",
    "end_date": null,
    "ad_schedule": []
  }
}
```

## File Naming Conventions

1. **Timestamps**: Use ISO 8601 format: `YYYY-MM-DD_HH-MM-SS`
2. **Versions**: Use semantic versioning: `v1.0.0`
3. **Exports**: Include project name and date: `{project_name}_export_2024-08-26.csv`
4. **Backups**: Include version: `{project_name}_backup_v1.0.0.zip`

## Project Operations Support

### Cloning Support
When cloning a project:
- Copy entire project structure
- Clear `outputs/` directory
- Clear `cache/` directory  
- Reset statistics in `metadata.json`
- Update project_id and timestamps
- Preserve `inputs/` and `configs/`

### Update Support
When updating a project:
- Preserve existing structure
- Version previous outputs (archive)
- Update metadata with modification tracking
- Maintain cache for unchanged data

### Template Support
Template projects stored in `templates/` with:
- Sample input files
- Default configurations
- Example outputs for reference

## Benefits of This Structure

1. **Isolation**: Each project is completely self-contained
2. **Reusability**: Easy to clone and modify for new campaigns
3. **Organization**: Clear separation of inputs, configs, and outputs
4. **Caching**: Reduces API costs through intelligent caching
5. **Auditability**: Complete logs and metadata tracking
6. **Scalability**: Supports multiple projects simultaneously
7. **Version Control**: Git-friendly structure for tracking changes
8. **Portability**: Projects can be zipped and shared

## Implementation Notes

- Use `pathlib` for cross-platform path handling
- Implement validation to ensure structure integrity
- Create directories lazily (only when needed)
- Include `.gitkeep` files in empty directories for version control
- Implement automatic cleanup for old cache files
- Use JSON for machine-readable configs, CSV for data files