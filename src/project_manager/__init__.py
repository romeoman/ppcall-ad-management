"""
Project Manager Module

Handles creation, management, and operations for isolated campaign projects.
Each project is self-contained with its own inputs, configurations, and outputs.
"""

from .project_structure import ProjectStructure, PROJECT_STRUCTURE_DEFINITION
from .project_config import ProjectConfig

__all__ = [
    'ProjectStructure',
    'PROJECT_STRUCTURE_DEFINITION',
    'ProjectConfig'
]