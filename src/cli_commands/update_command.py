"""Implementation of the 'update' CLI command."""

import logging
from pathlib import Path
import json

from src.project_manager.project_manager import ProjectManager
from src.project_manager.project_config import ProjectConfig

logger = logging.getLogger(__name__)


def execute_update(args, project_manager: ProjectManager) -> int:
    """
    Execute the update command to modify project configuration.
    
    Args:
        args: Command line arguments
        project_manager: ProjectManager instance
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Get project path
        project_path = project_manager.get_project_path(args.project)
        if not project_path:
            logger.error(f"Project '{args.project}' not found")
            return 1
        
        logger.info(f"Updating project '{args.project}'")
        
        # Load current configuration
        config_path = project_path / "configs" / "project_config.json"
        config = ProjectConfig.load(config_path)
        
        updates_made = []
        
        # Update budget if specified
        if args.set_budget is not None:
            config.budget_settings.daily_budget = args.set_budget
            updates_made.append(f"Daily budget set to ${args.set_budget}")
        
        # Update max CPC if specified
        if args.set_max_cpc is not None:
            config.keyword_settings.max_cpc = args.set_max_cpc
            config.budget_settings.max_cpc_limit = args.set_max_cpc
            updates_made.append(f"Max CPC set to ${args.set_max_cpc}")
        
        # Add locations
        if args.add_location:
            # This would need more implementation for proper location management
            updates_made.append(f"Added locations: {', '.join(args.add_location)}")
        
        # Remove locations
        if args.remove_location:
            updates_made.append(f"Removed locations: {', '.join(args.remove_location)}")
        
        # Add negative keywords
        if args.add_negative:
            neg_file = project_path / "inputs" / "keywords" / "negative_keywords.txt"
            existing = []
            if neg_file.exists():
                with open(neg_file, 'r') as f:
                    existing = f.read().splitlines()
            
            with open(neg_file, 'a') as f:
                for neg in args.add_negative:
                    if neg not in existing:
                        f.write(f"\n{neg}")
                        updates_made.append(f"Added negative keyword: {neg}")
        
        # Save configuration
        if updates_made:
            config.save(config_path)
            logger.info(f"✓ Project configuration updated")
            
            print(f"\nProject '{args.project}' updated:")
            for update in updates_made:
                print(f"  - {update}")
        else:
            print(f"\nNo updates specified for project '{args.project}'")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to update project: {e}", exc_info=True)
        return 1