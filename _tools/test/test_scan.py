"""Test suite for recipe scanner"""

import pytest
from pathlib import Path
from _tools.scan import RecipeScanner
from unittest.mock import Mock
from contextlib import contextmanager
import os
import yaml

@contextmanager
def as_cwd(path):
    """Context manager to temporarily change working directory"""
    old_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)

# Add this method to Path class
Path.as_cwd = as_cwd

@pytest.fixture
def scanner(test_data_dir):
    """Fixture providing a configured RecipeScanner instance"""
    return RecipeScanner(
        config_path=str(test_data_dir / '_tools/book.yml'),
        build_dir=str(test_data_dir / '_build')
    )

@pytest.fixture
def test_content_dirs(test_data_dir):
    """Create test content directories and files"""
    # Create section directories
    sections = ['01-appetizers', '02-main-dishes', 'desserts', '_tools']
    for section in sections:
        section_dir = test_data_dir / section
        section_dir.mkdir(exist_ok=True)
        
        # Add a sample recipe file in each section
        if section != '_tools':  # Skip creating files in _tools
            recipe_file = section_dir / 'sample.tex'
            recipe_file.touch()
    
    return test_data_dir

def test_scanner_initialization(scanner):
    """Test scanner initializes with correct paths"""
    assert scanner.config['title'] == 'Test Cookbook'
    assert scanner.build_dir.exists()
    assert scanner.config_path.name == 'book.yml'
    assert scanner.config_path.parent.name == '_tools'

def test_process_section_name(scanner):
    """Test section name processing"""
    scanner.config = Mock()
    
    assert scanner.process_section_name('01-main-dishes') == 'Main Dishes'
    assert scanner.process_section_name('desserts') == 'Desserts'

def test_scan_content_directories(test_data_dir, scanner, test_content_dirs):
    """Test directory scanning"""
    with Path.cwd().joinpath(test_data_dir).as_cwd():
        sections = scanner.scan_content_directories()
        assert sections['01-appetizers'] == 'Appetizers'
        assert sections['02-main-dishes'] == 'Main Dishes'
        assert sections['desserts'] == 'Desserts'
        assert '_tools' not in sections

def test_detect_changes(scanner, clean_build_dir):
    """Test change detection between builds"""
    existing = {
        'recipes': {
            '01-appetizers/bruschetta.tex': {
                'mtime': '2024-01-01T00:00:00Z'
            }
        }
    }
    
    new_files = {
        '01-appetizers/bruschetta.tex': {
            'mtime': '2024-01-02T00:00:00Z'  # Modified
        }
    }
    
    updated = scanner.detect_changes(existing, new_files)
    assert updated['01-appetizers/bruschetta.tex']['changed'] == True 

def test_load_invalid_config(scanner, tmp_path):
    """Test handling of invalid configuration file"""
    invalid_config = tmp_path / "invalid.yml"
    invalid_config.write_text("invalid: yaml: :")
    
    with pytest.raises(yaml.YAMLError):
        RecipeScanner(config_path=str(invalid_config))

def test_load_missing_required_fields(scanner, tmp_path):
    """Test detection of missing required configuration fields"""
    incomplete_config = tmp_path / "incomplete.yml"
    incomplete_config.write_text("title: Test")
    
    with pytest.raises(ValueError) as exc_info:
        RecipeScanner(config_path=str(incomplete_config))
    assert "Missing required config fields" in str(exc_info.value)

def test_scan_empty_directory(scanner, tmp_path):
    """Test scanning an empty directory"""
    with tmp_path.as_cwd():
        sections = scanner.scan_content_directories()
        assert len(sections) == 0

def test_update_metadata_preserves_packages(scanner, clean_build_dir):
    """Test that updating metadata preserves existing package information"""
    existing = {
        'packages': ['geometry', 'graphicx'],
        'recipes': {},
        'sections': {}
    }
    
    # Write existing metadata
    with open(scanner.metadata_path, 'w') as f:
        yaml.dump(existing, f)
    
    # Update with new data
    new_metadata = scanner.update_metadata({'section1': 'Section 1'}, {})
    assert 'geometry' in new_metadata['packages']
    assert 'graphicx' in new_metadata['packages'] 