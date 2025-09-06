"""
Unit tests for ProjectManager class.

Tests project creation, validation, cloning, and management operations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import json
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.project_manager.project_manager import ProjectManager
from src.project_manager.project_config import ProjectConfig, LocationSettings, KeywordSettings
from src.project_manager.project_structure import ProjectMetadata


class TestProjectManager:
    """Test suite for ProjectManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def project_manager(self, temp_dir):
        """Create a ProjectManager instance with temporary base path."""
        return ProjectManager(base_path=str(temp_dir))
    
    def test_initialization(self, temp_dir):
        """Test ProjectManager initialization."""
        pm = ProjectManager(base_path=str(temp_dir))
        assert pm.base_path == temp_dir
        assert temp_dir.exists()
    
    def test_create_project_basic(self, project_manager):
        """Test basic project creation."""
        project_name = "test_campaign"
        project_path = project_manager.create_project(project_name)
        
        assert project_path.exists()
        assert project_path.name == project_name
        
        # Check main directories exist
        assert (project_path / "inputs").exists()
        assert (project_path / "configs").exists()
        assert (project_path / "outputs").exists()
        assert (project_path / "cache").exists()
        assert (project_path / "logs").exists()
        
        # Check metadata file
        metadata_path = project_path / "metadata.json"
        assert metadata_path.exists()
        
        metadata = ProjectMetadata.load(metadata_path)
        assert metadata.project_name == project_name
        assert metadata.status == "active"
    
    def test_create_project_with_config(self, project_manager):
        """Test project creation with custom configuration."""
        project_name = "configured_campaign"
        
        # Create custom config
        config = ProjectConfig(
            project_name=project_name,
            target_platforms=["google_ads", "bing_ads"],
            language="es",
            currency="EUR"
        )
        
        project_path = project_manager.create_project(
            project_name, 
            config=config
        )
        
        # Load saved config
        saved_config = ProjectConfig.load(
            project_path / "configs" / "project_config.json"
        )
        
        assert saved_config.project_name == project_name
        assert "google_ads" in saved_config.target_platforms
        assert "bing_ads" in saved_config.target_platforms
        assert saved_config.language == "es"
        assert saved_config.currency == "EUR"
    
    def test_create_project_already_exists(self, project_manager):
        """Test error when creating duplicate project."""
        project_name = "duplicate_project"
        
        # Create first project
        project_manager.create_project(project_name)
        
        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            project_manager.create_project(project_name)
    
    def test_validate_project(self, project_manager):
        """Test project structure validation."""
        project_name = "validation_test"
        project_manager.create_project(project_name)
        
        is_valid, issues = project_manager.validate_project(project_name)
        assert is_valid
        assert len(issues) == 0
    
    def test_validate_project_missing_dirs(self, project_manager):
        """Test validation with missing directories."""
        project_name = "broken_project"
        project_path = project_manager.base_path / project_name
        project_path.mkdir()
        
        # Create only partial structure
        (project_path / "inputs").mkdir()
        (project_path / "configs").mkdir()
        # Missing: outputs, cache, logs
        
        is_valid, issues = project_manager.validate_project(project_name)
        assert not is_valid
        assert len(issues) > 0
        assert any("outputs" in issue for issue in issues)
    
    def test_list_projects(self, project_manager):
        """Test listing all projects."""
        # Create multiple projects
        projects_to_create = ["project_1", "project_2", "project_3"]
        
        for name in projects_to_create:
            project_manager.create_project(name)
        
        projects = project_manager.list_projects()
        assert len(projects) == 3
        
        project_names = [p["project_name"] for p in projects]
        assert all(name in project_names for name in projects_to_create)
        
        # Check project info structure
        for project in projects:
            assert "project_name" in project
            assert "path" in project
            assert "is_valid" in project
            assert project["is_valid"] == True
    
    def test_get_project_path(self, project_manager):
        """Test getting project path."""
        project_name = "path_test"
        created_path = project_manager.create_project(project_name)
        
        retrieved_path = project_manager.get_project_path(project_name)
        assert retrieved_path == created_path
        
        # Test non-existent project
        non_existent_path = project_manager.get_project_path("non_existent")
        assert non_existent_path is None
    
    def test_clone_project(self, project_manager):
        """Test project cloning functionality."""
        source_name = "source_project"
        target_name = "cloned_project"
        
        # Create source project
        source_path = project_manager.create_project(source_name)
        
        # Add some test data to source
        test_file = source_path / "inputs" / "keywords" / "test_data.txt"
        test_file.write_text("test keywords")
        
        output_file = source_path / "outputs" / "keywords" / "generated.csv"
        output_file.write_text("keyword,volume\ntest,100")
        
        # Clone the project
        cloned_path = project_manager.clone_project(
            source_name, 
            target_name,
            clear_outputs=True,
            clear_cache=True
        )
        
        assert cloned_path.exists()
        assert cloned_path.name == target_name
        
        # Check input files are preserved
        cloned_test_file = cloned_path / "inputs" / "keywords" / "test_data.txt"
        assert cloned_test_file.exists()
        assert cloned_test_file.read_text() == "test keywords"
        
        # Check outputs are cleared
        cloned_output = cloned_path / "outputs" / "keywords" / "generated.csv"
        assert not cloned_output.exists()
        
        # Check metadata is updated
        metadata = ProjectMetadata.load(cloned_path / "metadata.json")
        assert metadata.project_name == target_name
        assert metadata.parent_project is not None
    
    def test_clone_project_preserve_outputs(self, project_manager):
        """Test cloning with preserved outputs."""
        source_name = "source_preserve"
        target_name = "cloned_preserve"
        
        source_path = project_manager.create_project(source_name)
        
        # Add output file
        output_file = source_path / "outputs" / "keywords" / "data.csv"
        output_file.write_text("preserved data")
        
        # Clone without clearing outputs
        cloned_path = project_manager.clone_project(
            source_name,
            target_name,
            clear_outputs=False,
            clear_cache=False
        )
        
        # Check outputs are preserved
        cloned_output = cloned_path / "outputs" / "keywords" / "data.csv"
        assert cloned_output.exists()
        assert cloned_output.read_text() == "preserved data"
    
    def test_clone_project_not_found(self, project_manager):
        """Test cloning non-existent project."""
        with pytest.raises(FileNotFoundError, match="not found"):
            project_manager.clone_project("non_existent", "target")
    
    def test_clone_project_target_exists(self, project_manager):
        """Test error when cloning to existing project."""
        source_name = "source"
        target_name = "target"
        
        project_manager.create_project(source_name)
        project_manager.create_project(target_name)
        
        with pytest.raises(ValueError, match="already exists"):
            project_manager.clone_project(source_name, target_name)
    
    def test_delete_project(self, project_manager):
        """Test project deletion."""
        project_name = "to_delete"
        project_manager.create_project(project_name)
        
        # Delete without confirmation should fail
        result = project_manager.delete_project(project_name, confirm=False)
        assert result == False
        assert project_manager.get_project_path(project_name) is not None
        
        # Delete with confirmation should succeed
        result = project_manager.delete_project(project_name, confirm=True)
        assert result == True
        assert project_manager.get_project_path(project_name) is None
    
    def test_delete_nonexistent_project(self, project_manager):
        """Test deleting non-existent project."""
        result = project_manager.delete_project("non_existent", confirm=True)
        assert result == False
    
    def test_archive_project(self, project_manager):
        """Test project archiving."""
        project_name = "to_archive"
        project_path = project_manager.create_project(project_name)
        
        # Add some test data
        test_file = project_path / "inputs" / "test.txt"
        test_file.write_text("archive test data")
        
        # Archive the project
        archive_path = project_manager.archive_project(project_name)
        
        assert archive_path.exists()
        assert archive_path.suffix == ".zip"
        assert project_name in str(archive_path)
    
    def test_archive_nonexistent_project(self, project_manager):
        """Test archiving non-existent project."""
        with pytest.raises(FileNotFoundError, match="not found"):
            project_manager.archive_project("non_existent")
    
    def test_create_project_from_template(self, project_manager):
        """Test creating project from template."""
        template_name = "template_project"
        new_project = "from_template"
        
        # Create template project
        template_path = project_manager.create_project(template_name)
        
        # Customize template
        config = ProjectConfig.load(
            template_path / "configs" / "project_config.json"
        )
        config.target_platforms = ["google_ads", "bing_ads"]
        config.language = "fr"
        config.save(template_path / "configs" / "project_config.json")
        
        # Create new project from template
        new_path = project_manager.create_project(
            new_project, 
            template=template_name
        )
        
        assert new_path.exists()
        
        # Check config was copied
        new_config = ProjectConfig.load(
            new_path / "configs" / "project_config.json"
        )
        assert new_config.project_name == new_project
        assert new_config.language == "fr"
        assert "bing_ads" in new_config.target_platforms
    
    def test_sample_files_created(self, project_manager):
        """Test that sample input files are created."""
        project_name = "sample_test"
        project_path = project_manager.create_project(project_name)
        
        # Check sample files exist
        assert (project_path / "inputs" / "keywords" / "seed_keywords.txt").exists()
        assert (project_path / "inputs" / "keywords" / "negative_keywords.txt").exists()
        assert (project_path / "inputs" / "locations" / "cities.csv").exists()
        assert (project_path / "inputs" / "categories" / "services.csv").exists()
        
        # Check README exists
        assert (project_path / "README.md").exists()
        
        # Check content of sample files
        seed_keywords = (project_path / "inputs" / "keywords" / "seed_keywords.txt").read_text()
        assert "plumbing services" in seed_keywords
    
    def test_config_validation(self, project_manager):
        """Test project configuration validation."""
        project_name = "validation_config"
        project_path = project_manager.create_project(project_name)
        
        config_path = project_path / "configs" / "project_config.json"
        config = ProjectConfig.load(config_path)
        
        # Validate default config
        is_valid, errors = config.validate()
        assert is_valid
        assert len(errors) == 0
        
        # Create invalid config
        config.target_platforms = []  # Empty platforms list
        is_valid, errors = config.validate()
        assert not is_valid
        assert any("platform" in error for error in errors)