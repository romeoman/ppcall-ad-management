"""Implementation of the 'list' CLI command."""

import logging
from datetime import datetime
from pathlib import Path
from tabulate import tabulate

from src.project_manager.project_manager import ProjectManager

logger = logging.getLogger(__name__)


def execute_list(args, project_manager: ProjectManager) -> int:
    """
    Execute the list command to display all projects.
    
    Args:
        args: Command line arguments
        project_manager: ProjectManager instance
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Get all projects
        projects = project_manager.list_projects()
        
        if not projects:
            print("No projects found.")
            print("\nCreate a new project with: ppc create <project_name>")
            return 0
        
        # Filter projects based on status
        if args.filter != 'all':
            projects = [p for p in projects if p.get('status', 'active') == args.filter]
        
        if not projects:
            print(f"No {args.filter} projects found.")
            return 0
        
        if args.detailed:
            # Detailed view
            display_detailed_projects(projects)
        else:
            # Simple table view
            display_projects_table(projects)
        
        # Show summary
        print(f"\nTotal projects: {len(projects)}")
        
        # Count by status
        status_counts = {}
        for project in projects:
            status = project.get('status', 'active')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if len(status_counts) > 1:
            print("Status breakdown:", ", ".join(f"{s}: {c}" for s, c in status_counts.items()))
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        return 1


def display_projects_table(projects):
    """
    Display projects in a simple table format.
    
    Args:
        projects: List of project dictionaries
    """
    # Prepare table data
    table_data = []
    for project in projects:
        # Parse dates
        created = project.get('created_date', '')
        if created:
            try:
                created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                created = created_dt.strftime('%Y-%m-%d')
            except:
                pass
        
        last_modified = project.get('last_modified', '')
        if last_modified:
            try:
                modified_dt = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                last_modified = modified_dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        # Get statistics
        stats = project.get('statistics', {})
        total_keywords = stats.get('total_keywords', 0)
        total_ad_groups = stats.get('total_ad_groups', 0)
        
        # Validation status
        is_valid = "✓" if project.get('is_valid', False) else "✗"
        
        table_data.append([
            project.get('project_name', 'Unknown'),
            project.get('status', 'active').capitalize(),
            created,
            last_modified,
            f"{total_keywords:,}",
            f"{total_ad_groups:,}",
            is_valid
        ])
    
    # Sort by project name
    table_data.sort(key=lambda x: x[0])
    
    # Display table
    headers = ['Project Name', 'Status', 'Created', 'Last Modified', 
               'Keywords', 'Ad Groups', 'Valid']
    print("\n" + tabulate(table_data, headers=headers, tablefmt='grid'))


def display_detailed_projects(projects):
    """
    Display projects in detailed format.
    
    Args:
        projects: List of project dictionaries
    """
    for i, project in enumerate(projects, 1):
        print(f"\n{'='*60}")
        print(f"Project #{i}: {project.get('project_name', 'Unknown')}")
        print(f"{'='*60}")
        
        # Basic information
        print(f"Status: {project.get('status', 'active').capitalize()}")
        print(f"Path: {project.get('path', 'Unknown')}")
        print(f"Created: {project.get('created_date', 'Unknown')}")
        print(f"Last Modified: {project.get('last_modified', 'Unknown')}")
        
        # Description
        description = project.get('description', '')
        if description:
            print(f"Description: {description}")
        
        # Tags
        tags = project.get('tags', [])
        if tags:
            print(f"Tags: {', '.join(tags)}")
        
        # Statistics
        stats = project.get('statistics', {})
        if stats:
            print("\nStatistics:")
            print(f"  - Total Keywords: {stats.get('total_keywords', 0):,}")
            print(f"  - Total Ad Groups: {stats.get('total_ad_groups', 0):,}")
            print(f"  - Total Locations: {stats.get('total_locations', 0):,}")
            print(f"  - API Calls Made: {stats.get('api_calls_made', 0):,}")
            
            last_gen = stats.get('last_generation_date')
            if last_gen:
                print(f"  - Last Generation: {last_gen}")
        
        # Parent project
        parent = project.get('parent_project')
        if parent:
            print(f"Cloned From: {parent}")
        
        # Validation
        is_valid = project.get('is_valid', False)
        if is_valid:
            print("Validation: ✓ Valid")
        else:
            print("Validation: ✗ Invalid")
            issues = project.get('validation_issues', [])
            if issues:
                print("Issues:")
                for issue in issues[:5]:  # Show first 5 issues
                    print(f"  - {issue}")
                if len(issues) > 5:
                    print(f"  ... and {len(issues) - 5} more")
        
        # Error if present
        error = project.get('error')
        if error:
            print(f"Error: {error}")
    
    print(f"\n{'='*60}")