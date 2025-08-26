"""Mock API response fixtures for testing."""

import json
from typing import Dict, List, Any


class APIResponseFixtures:
    """Container for mock API responses."""

    @staticmethod
    def dataforseo_keyword_data_response() -> Dict[str, Any]:
        """Mock response from DataForSEO Keywords Data API."""
        return {
            "version": "0.1.20241204",
            "status_code": 20000,
            "status_message": "Ok.",
            "time": "0.0900 sec.",
            "cost": 0.05,
            "tasks_count": 1,
            "tasks_error": 0,
            "tasks": [
                {
                    "id": "01091234-5678-9012-3456-789012345678",
                    "status_code": 20000,
                    "status_message": "Ok.",
                    "time": "0.0900 sec.",
                    "cost": 0.05,
                    "result_count": 1,
                    "path": ["v3", "keywords_data", "google_ads", "search_volume", "live"],
                    "data": {
                        "keywords": ["project management software", "task management tool"],
                        "location_code": 2840,
                        "language_code": "en"
                    },
                    "result": [
                        {
                            "keyword": "project management software",
                            "location_code": 2840,
                            "language_code": "en",
                            "search_partners": False,
                            "keyword_annotations": {
                                "concepts": [
                                    {
                                        "name": "Software",
                                        "concept_group": {
                                            "name": "Software",
                                            "type": "NON_BRAND"
                                        }
                                    }
                                ]
                            },
                            "monthly_searches": [
                                {"year": 2024, "month": 11, "search_volume": 60500},
                                {"year": 2024, "month": 10, "search_volume": 74000},
                                {"year": 2024, "month": 9, "search_volume": 60500},
                                {"year": 2024, "month": 8, "search_volume": 49500},
                                {"year": 2024, "month": 7, "search_volume": 49500},
                                {"year": 2024, "month": 6, "search_volume": 49500},
                                {"year": 2024, "month": 5, "search_volume": 60500},
                                {"year": 2024, "month": 4, "search_volume": 60500},
                                {"year": 2024, "month": 3, "search_volume": 60500},
                                {"year": 2024, "month": 2, "search_volume": 60500},
                                {"year": 2024, "month": 1, "search_volume": 60500},
                                {"year": 2023, "month": 12, "search_volume": 49500}
                            ],
                            "search_volume": 60500,
                            "competition": "HIGH",
                            "competition_index": 100,
                            "low_top_of_page_bid": 3.41,
                            "high_top_of_page_bid": 29.68
                        },
                        {
                            "keyword": "task management tool",
                            "location_code": 2840,
                            "language_code": "en",
                            "search_partners": False,
                            "monthly_searches": [
                                {"year": 2024, "month": 11, "search_volume": 12100},
                                {"year": 2024, "month": 10, "search_volume": 14800},
                                {"year": 2024, "month": 9, "search_volume": 12100}
                            ],
                            "search_volume": 12100,
                            "competition": "HIGH",
                            "competition_index": 95,
                            "low_top_of_page_bid": 2.85,
                            "high_top_of_page_bid": 24.12
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def dataforseo_keyword_suggestions_response() -> Dict[str, Any]:
        """Mock response from DataForSEO Keywords for Keywords API."""
        return {
            "version": "0.1.20241204",
            "status_code": 20000,
            "status_message": "Ok.",
            "time": "0.1234 sec.",
            "cost": 0.075,
            "tasks_count": 1,
            "tasks_error": 0,
            "tasks": [
                {
                    "id": "01091234-5678-9012-3456-789012345678",
                    "status_code": 20000,
                    "status_message": "Ok.",
                    "time": "0.1234 sec.",
                    "cost": 0.075,
                    "result_count": 1,
                    "path": ["v3", "keywords_data", "google_ads", "keywords_for_keywords", "live"],
                    "data": {
                        "keywords": ["project management"],
                        "location_code": 2840,
                        "language_code": "en"
                    },
                    "result": [
                        {
                            "keyword": "project management software",
                            "search_volume": 60500,
                            "competition": "HIGH",
                            "competition_index": 100,
                            "low_top_of_page_bid": 3.41,
                            "high_top_of_page_bid": 29.68
                        },
                        {
                            "keyword": "project management tools",
                            "search_volume": 33100,
                            "competition": "HIGH",
                            "competition_index": 98,
                            "low_top_of_page_bid": 2.95,
                            "high_top_of_page_bid": 25.50
                        },
                        {
                            "keyword": "best project management software",
                            "search_volume": 18100,
                            "competition": "HIGH",
                            "competition_index": 100,
                            "low_top_of_page_bid": 4.12,
                            "high_top_of_page_bid": 35.20
                        },
                        {
                            "keyword": "free project management software",
                            "search_volume": 14800,
                            "competition": "HIGH",
                            "competition_index": 95,
                            "low_top_of_page_bid": 2.25,
                            "high_top_of_page_bid": 18.90
                        },
                        {
                            "keyword": "online project management",
                            "search_volume": 8100,
                            "competition": "HIGH",
                            "competition_index": 92,
                            "low_top_of_page_bid": 2.75,
                            "high_top_of_page_bid": 22.30
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def serp_api_response() -> Dict[str, Any]:
        """Mock response from SERP API."""
        return {
            "search_metadata": {
                "id": "674abc123def456789",
                "status": "Success",
                "created_at": "2024-01-09T10:30:00Z",
                "processed_at": "2024-01-09T10:30:02Z",
                "total_time_taken": 2.15
            },
            "search_parameters": {
                "q": "project management software",
                "location": "United States",
                "google_domain": "google.com",
                "gl": "us",
                "hl": "en",
                "num": 10
            },
            "organic_results": [
                {
                    "position": 1,
                    "title": "Best Project Management Software 2024",
                    "link": "https://www.example1.com/project-management",
                    "displayed_link": "www.example1.com › project-management",
                    "snippet": "Compare the best project management software...",
                    "snippet_highlighted_words": ["project", "management", "software"]
                },
                {
                    "position": 2,
                    "title": "Top 10 Project Management Tools",
                    "link": "https://www.example2.com/tools",
                    "displayed_link": "www.example2.com › tools",
                    "snippet": "Discover the top project management tools...",
                    "snippet_highlighted_words": ["project", "management", "tools"]
                }
            ],
            "related_searches": [
                {"query": "free project management software"},
                {"query": "project management software for small business"},
                {"query": "best project management tools 2024"},
                {"query": "project management software comparison"}
            ]
        }

    @staticmethod
    def firecrawl_scrape_response() -> Dict[str, Any]:
        """Mock response from FireCrawl API."""
        return {
            "success": True,
            "data": {
                "url": "https://www.example.com/landing-page",
                "content": "# Best Project Management Software\n\nStreamline your workflow with our powerful project management solution.\n\n## Features\n- Task tracking\n- Team collaboration\n- Real-time updates\n- Gantt charts\n- Resource management\n\n## Pricing\nStarting at $15/user/month\n\n## Get Started\nSign up for a free 14-day trial",
                "markdown": "# Best Project Management Software\n\nStreamline your workflow...",
                "metadata": {
                    "title": "Best Project Management Software - Example Corp",
                    "description": "Streamline your workflow with powerful project management",
                    "language": "en",
                    "keywords": "project management, task tracking, team collaboration",
                    "ogTitle": "Best Project Management Software",
                    "ogDescription": "Streamline your workflow with our solution",
                    "ogImage": "https://www.example.com/og-image.jpg"
                },
                "llm_extraction": {
                    "headline": "Best Project Management Software",
                    "subheadline": "Streamline your workflow with our powerful project management solution",
                    "features": [
                        "Task tracking",
                        "Team collaboration",
                        "Real-time updates",
                        "Gantt charts",
                        "Resource management"
                    ],
                    "pricing": {
                        "starting_price": "$15/user/month",
                        "trial_period": "14 days"
                    },
                    "call_to_action": "Sign up for a free 14-day trial"
                }
            }
        }

    @staticmethod
    def error_response_rate_limit() -> Dict[str, Any]:
        """Mock rate limit error response."""
        return {
            "error": {
                "code": 429,
                "message": "Rate limit exceeded. Please try again later.",
                "details": {
                    "limit": 100,
                    "remaining": 0,
                    "reset_at": "2024-01-09T11:00:00Z"
                }
            }
        }

    @staticmethod
    def error_response_auth() -> Dict[str, Any]:
        """Mock authentication error response."""
        return {
            "error": {
                "code": 401,
                "message": "Authentication failed. Invalid API credentials.",
                "details": {
                    "reason": "Invalid API key or credentials"
                }
            }
        }

    @staticmethod
    def error_response_server() -> Dict[str, Any]:
        """Mock server error response."""
        return {
            "error": {
                "code": 500,
                "message": "Internal server error. Please try again later.",
                "details": {
                    "request_id": "req_123456789"
                }
            }
        }

    @staticmethod
    def cached_response() -> Dict[str, Any]:
        """Mock cached response structure."""
        return {
            "cached": True,
            "cached_at": "2024-01-09T10:00:00Z",
            "ttl": 3600,
            "data": {
                "keyword": "cached keyword",
                "search_volume": 1000,
                "competition": "LOW"
            }
        }