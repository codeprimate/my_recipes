"""Common test fixtures and configuration"""

import pytest
from pathlib import Path
import shutil
import yaml

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary test data directory structure"""
    # Create test directories
    recipe_dirs = ['01-appetizers', '02-main-dishes', 'desserts']
    for dir_name in recipe_dirs:
        (tmp_path / dir_name).mkdir()
    
    # Create test recipe files
    (tmp_path / '01-appetizers/bruschetta.tex').write_text(
        '\\begin{document}\nBruschetta Recipe\n\\end{document}'
    )
    
    # Create test config
    config = {
        'title': 'Test Cookbook',
        'authorship': {'author': 'Test Author'},
        'template': '_templates/book.tex',
        'style': {'documentclass': 'article'},
        'build': {'output_dir': '_build'}
    }
    
    (tmp_path / '_tools').mkdir()
    (tmp_path / '_tools/book.yml').write_text(yaml.dump(config))
    
    # Create build directory
    (tmp_path / '_build').mkdir()
    
    return tmp_path

@pytest.fixture
def clean_build_dir(test_data_dir):
    """Ensure clean build directory between tests"""
    build_dir = test_data_dir / '_build'
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    return build_dir 