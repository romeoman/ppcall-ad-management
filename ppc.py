#!/usr/bin/env python3
"""
PPC Campaign Manager CLI

A comprehensive command-line interface for managing PPC (Pay-Per-Click) 
advertising campaigns with support for keyword research, ad group generation,
and campaign exports.
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from typing import Optional
import asyncio
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.project_manager.project_manager import ProjectManager
from src.project_manager.project_config import ProjectConfig

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_parser():
    """Set up the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog='ppc',
        description='PPC Campaign Manager - Automate your PPC campaign creation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ppc create my_campaign              # Create a new campaign project
  ppc research --project my_campaign  # Research and expand keywords
  ppc generate --project my_campaign  # Generate ad groups
  ppc export --project my_campaign    # Export campaign files
  ppc analyze --project my_campaign   # Analyze competition
  ppc list                            # List all projects
  ppc clone old_campaign new_campaign # Clone an existing campaign
        """
    )
    
    # Global arguments
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress non-error output')
    
    # Create subparsers
    subparsers = parser.add_subparsers(
        title='Commands',
        description='Available commands for PPC campaign management',
        dest='command',
        help='Command to execute'
    )
    
    # CREATE command
    parser_create = subparsers.add_parser(
        'create',
        help='Create a new PPC campaign project',
        description='Initialize a new project with folder structure and configuration'
    )
    parser_create.add_argument(
        'project_name',
        help='Name of the project to create'
    )
    parser_create.add_argument(
        '--template', '-t',
        help='Use an existing project as template'
    )
    parser_create.add_argument(
        '--industry', '-i',
        choices=['plumbing', 'hvac', 'electrical', 'roofing', 'general'],
        default='general',
        help='Industry type for default configurations'
    )
    parser_create.add_argument(
        '--platforms', '-p',
        nargs='+',
        choices=['google', 'bing', 'both'],
        default=['both'],
        help='Target advertising platforms'
    )
    parser_create.add_argument(
        '--interactive', '-I',
        action='store_true',
        help='Use interactive mode for configuration'
    )
    
    # RESEARCH command
    parser_research = subparsers.add_parser(
        'research',
        help='Research and expand keywords',
        description='Expand seed keywords using APIs and analyze search data'
    )
    parser_research.add_argument(
        '--project', '-p',
        required=True,
        help='Project name or path'
    )
    parser_research.add_argument(
        '--seeds', '-s',
        help='Path to seed keywords file (overrides project seeds)'
    )
    parser_research.add_argument(
        '--depth', '-d',
        type=int,
        default=2,
        choices=[1, 2, 3],
        help='Keyword expansion depth (1=basic, 2=moderate, 3=extensive)'
    )
    parser_research.add_argument(
        '--locations', '-l',
        help='Path to locations file (overrides project locations)'
    )
    parser_research.add_argument(
        '--min-volume',
        type=int,
        default=10,
        help='Minimum monthly search volume'
    )
    parser_research.add_argument(
        '--max-cpc',
        type=float,
        default=50.0,
        help='Maximum cost-per-click filter'
    )
    parser_research.add_argument(
        '--platform',
        choices=['google', 'bing', 'both'],
        default='both',
        help='Platform for keyword research'
    )
    
    # GENERATE command
    parser_generate = subparsers.add_parser(
        'generate',
        help='Generate ad groups from keywords',
        description='Organize keywords into ad groups with match types'
    )
    parser_generate.add_argument(
        '--project', '-p',
        required=True,
        help='Project name or path'
    )
    parser_generate.add_argument(
        '--match-types', '-m',
        nargs='+',
        choices=['broad', 'phrase', 'exact'],
        default=['broad', 'phrase', 'exact'],
        help='Match types to generate'
    )
    parser_generate.add_argument(
        '--group-by',
        choices=['service', 'location', 'both'],
        default='both',
        help='How to group keywords into ad groups'
    )
    parser_generate.add_argument(
        '--max-keywords-per-group',
        type=int,
        default=20,
        help='Maximum keywords per ad group'
    )
    parser_generate.add_argument(
        '--include-negatives',
        action='store_true',
        help='Generate negative keyword lists'
    )
    
    # EXPORT command
    parser_export = subparsers.add_parser(
        'export',
        help='Export campaign data',
        description='Export campaign data in platform-specific formats'
    )
    parser_export.add_argument(
        '--project', '-p',
        required=True,
        help='Project name or path'
    )
    parser_export.add_argument(
        '--format', '-f',
        choices=['google', 'bing', 'csv', 'all'],
        default='all',
        help='Export format'
    )
    parser_export.add_argument(
        '--output', '-o',
        help='Output directory (default: project/outputs/exports/)'
    )
    parser_export.add_argument(
        '--include-settings',
        action='store_true',
        help='Include campaign settings in export'
    )
    parser_export.add_argument(
        '--zip',
        action='store_true',
        help='Create ZIP archive of exports'
    )
    
    # ANALYZE command
    parser_analyze = subparsers.add_parser(
        'analyze',
        help='Analyze competition and opportunities',
        description='Analyze competitor keywords and identify gaps'
    )
    parser_analyze.add_argument(
        '--project', '-p',
        required=True,
        help='Project name or path'
    )
    parser_analyze.add_argument(
        '--competitors', '-c',
        nargs='+',
        help='Competitor URLs to analyze'
    )
    parser_analyze.add_argument(
        '--spyfu',
        help='Path to SpyFu export CSV'
    )
    parser_analyze.add_argument(
        '--scrape-landing-pages',
        action='store_true',
        help='Scrape and analyze competitor landing pages'
    )
    parser_analyze.add_argument(
        '--identify-gaps',
        action='store_true',
        help='Identify keyword opportunities'
    )
    
    # LIST command
    parser_list = subparsers.add_parser(
        'list',
        help='List all projects',
        description='Display all PPC campaign projects'
    )
    parser_list.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='Show detailed project information'
    )
    parser_list.add_argument(
        '--filter', '-f',
        choices=['active', 'archived', 'all'],
        default='active',
        help='Filter projects by status'
    )
    
    # CLONE command
    parser_clone = subparsers.add_parser(
        'clone',
        help='Clone an existing project',
        description='Create a copy of an existing project for a new campaign'
    )
    parser_clone.add_argument(
        'source',
        help='Source project to clone from'
    )
    parser_clone.add_argument(
        'target',
        help='Name for the new project'
    )
    parser_clone.add_argument(
        '--clear-outputs',
        action='store_true',
        default=True,
        help='Clear output files in cloned project'
    )
    parser_clone.add_argument(
        '--clear-cache',
        action='store_true',
        default=True,
        help='Clear cached API responses'
    )
    
    # UPDATE command
    parser_update = subparsers.add_parser(
        'update',
        help='Update project configuration',
        description='Modify project settings and configuration'
    )
    parser_update.add_argument(
        '--project', '-p',
        required=True,
        help='Project name or path'
    )
    parser_update.add_argument(
        '--add-location',
        action='append',
        help='Add a location to target'
    )
    parser_update.add_argument(
        '--remove-location',
        action='append',
        help='Remove a location'
    )
    parser_update.add_argument(
        '--set-budget',
        type=float,
        help='Set daily budget'
    )
    parser_update.add_argument(
        '--set-max-cpc',
        type=float,
        help='Set maximum CPC'
    )
    parser_update.add_argument(
        '--add-negative',
        action='append',
        help='Add negative keyword'
    )
    
    return parser


def main():
    """Main entry point for the PPC CLI."""
    parser = setup_parser()
    args = parser.parse_args()
    
    # Set up logging based on verbosity
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if a command was provided
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Initialize project manager
        project_manager = ProjectManager()
        
        # Route to appropriate command handler
        if args.command == 'create':
            from src.cli_commands.create_command import execute_create
            return execute_create(args, project_manager)
            
        elif args.command == 'research':
            from src.cli_commands.research_command import execute_research
            return asyncio.run(execute_research(args, project_manager))
            
        elif args.command == 'generate':
            from src.cli_commands.generate_command import execute_generate
            return execute_generate(args, project_manager)
            
        elif args.command == 'export':
            from src.cli_commands.export_command import execute_export
            return execute_export(args, project_manager)
            
        elif args.command == 'analyze':
            from src.cli_commands.analyze_command import execute_analyze
            return asyncio.run(execute_analyze(args, project_manager))
            
        elif args.command == 'list':
            from src.cli_commands.list_command import execute_list
            return execute_list(args, project_manager)
            
        elif args.command == 'clone':
            from src.cli_commands.clone_command import execute_clone
            return execute_clone(args, project_manager)
            
        elif args.command == 'update':
            from src.cli_commands.update_command import execute_update
            return execute_update(args, project_manager)
        
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Error executing command: {e}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())