import pytest
import shutil
import yaml
from pathlib import Path

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary test data directory with required structure"""
    # Create test directory structure
    tools_dir = tmp_path / '_tools'
    tools_dir.mkdir()
    
    # Create test config file
    config = {
        'title': 'Test Cookbook',
        'authorship': 'Test Author',
        'template': 'book',
        'style': 'cookbook',
        'build': {'output': 'pdf'}
    }
    
    config_path = tools_dir / 'book.yml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    # Create build directory
    build_dir = tmp_path / '_build'
    build_dir.mkdir()
    
    return tmp_path

@pytest.fixture
def clean_build_dir(test_data_dir):
    """Ensure clean build directory for each test"""
    build_dir = test_data_dir / '_build'
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    return build_dir 