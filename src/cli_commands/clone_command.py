"""Implementation of the 'clone' CLI command."""

import logging

from src.project_manager.project_manager import ProjectManager

logger = logging.getLogger(__name__)


def execute_clone(args, project_manager: ProjectManager) -> int:
    """
    Execute the clone command to duplicate an existing project.
    
    Args:
        args: Command line arguments
        project_manager: ProjectManager instance
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        source = args.source
        target = args.target
        
        # Check if source exists
        if not project_manager.get_project_path(source):
            logger.error(f"Source project '{source}' not found")
            return 1
        
        # Check if target already exists
        if project_manager.get_project_path(target):
            logger.error(f"Target project '{target}' already exists")
            return 1
        
        # Clone the project
        logger.info(f"Cloning project '{source}' to '{target}'")
        project_path = project_manager.clone_project(
            source,
            target,
            clear_outputs=args.clear_outputs,
            clear_cache=args.clear_cache
        )
        
        logger.info(f"✓ Project cloned successfully to {project_path}")
        print(f"\nProject cloned to: {project_path}")
        
        if args.clear_outputs:
            print("Output files have been cleared.")
        if args.clear_cache:
            print("Cache has been cleared.")
        
        print(f"\nYou can now work with the cloned project:")
        print(f"  ppc research --project {target}")
        print(f"  ppc generate --project {target}")
        print(f"  ppc export --project {target}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to clone project: {e}")
        return 1