# Consistent Naming Conventions, File Structure, and Architecture Patterns

This document outlines guidelines for maintaining consistency in the Python application "PPC Keyword Automator". These standards ensure code readability, maintainability, and scalability when developing with tools like Claude Opus in Cursor IDE. Follow PEP 8 where applicable, with customizations for this project.

## Naming Conventions

Use clear, descriptive names to make the code self-explanatory. Avoid abbreviations unless they are standard (e.g., API, CSV).

- **Variables and Functions**: Use snake_case (lowercase with underscores).
  - Examples: `seed_keywords`, `generate_ad_groups()`, `fetch_keyword_metrics()`.
  - For constants: UPPER_SNAKE_CASE, e.g., `DEFAULT_CATEGORIES = ["emergency_plumbing", "toilet_repairs"]`.

- **Classes and Models**: Use CamelCase (PascalCase).
  - Examples: `KeywordSchema`, `AdGroupGenerator`.
  - Pydantic models should end with "Schema" for clarity, e.g., `NegativeKeywordSchema`.

- **Files and Modules**: Use snake_case for filenames.
  - Examples: `keyword_expander.py`, `api_connectors.py`.
  - Avoid hyphens; use underscores.

- **Other Rules**:
  - Prefix private methods/variables with a single underscore, e.g., `_validate_inputs()`.
  - Use meaningful names: Prefer `city_list` over `cl`; `expand_keywords_with_locations()` over `exp_kw()`.
  - For API-related: Prefix with api_, e.g., `api_data4seo_fetch()`.

## File Structure

Organize the project in a modular directory structure to separate concerns. Root directory: `ppc_keyword_automator/`.

- **Top-Level Structure**:
  - `src/`: Core source code.
  - `configs/`: Configuration files (e.g., API keys in .env, default categories in YAML).
  - `data/`: Input/output files (e.g., seeds.txt, output CSVs). Subdirs: `inputs/`, `outputs/`.
  - `tests/`: Unit tests.
  - `docs/`: Documentation (e.g., this file).
  - `requirements.txt`: Dependencies.
  - `main.py`: Entry point script.

- **Inside src/**:
  - `models/`: Pydantic schemas (e.g., `keyword_schema.py`).
  - `utils/`: Helper functions (e.g., `csv_utils.py` for reading/writing CSVs, `logger.py`).
  - `api/`: API integrations (e.g., `dataforseo_connector.py`, `firecrawl_scraper.py`).
  - `core/`: Business logic (e.g., `keyword_expander.py`, `ad_group_generator.py`, `competition_analyzer.py`).
  - `cli/`: Command-line interface (e.g., `parser.py` using argparse).

- **Example Tree**:

| Directory/File | Purpose |
|---------------|---------|
| src/models/keyword_schema.py | Defines Pydantic models for keywords and negatives. |
| src/api/data4seo_connector.py | Handles Data4SEO API calls. |
| src/core/keyword_expander.py | Logic for expanding and categorizing keywords. |
| configs/defaults.yaml | YAML for default categories and negatives. |
| main.py | Parses args, orchestrates modules, generates outputs. |

- **Best Practices**:
  - One module per responsibility (e.g., separate file for each API).
  - Use `__init__.py` for packages.
  - Keep files under 500 lines; split if needed.

## Architecture Patterns

Follow a modular, pipeline-based architecture for this script-based app. Emphasize separation of concerns, data validation, and error handling.

- **Overall Pattern**: ETL-like Pipeline (Extract from APIs/inputs, Transform data, Load to CSVs).
  - Input → Validation (Pydantic) → Processing → Output.

- **Key Patterns**:
  - **Modular Design**: Break into independent modules (e.g., API calls in one, data processing in another). Use dependency injection for flexibility (e.g., pass configs to classes).
  - **Data Validation**: Always use Pydantic for inputs/outputs. Example: Define `class Keyword(BaseModel): term: str; category: str;`.
  - **Error Handling**: Use try-except blocks; log errors with logging module. Retry API calls with tenacity.
  - **Command-Line Driven**: Use argparse for inputs; no UI.
  - **Testing**: Write unit tests for each module (e.g., test keyword combination logic).

- **Component Interactions** (Flow):
  1. `main.py` parses CLI args.
  2. Loads data/models.
  3. Calls core modules (e.g., expand keywords, generate ad groups).
  4. Integrates APIs as needed.
  5. Exports via utils.

Adhering to these ensures the app remains extensible (e.g., add new APIs easily) and consistent across development. Reference this in Claude.md as: "- **Use consistent naming conventions, file structure, and architecture patterns**, use information from file structure.md".