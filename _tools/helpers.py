"""Shared helper functions for recipe book tools"""

import yaml
from pathlib import Path
from typing import Dict, List

def load_config(config_path: Path) -> dict:
    """Load and validate book configuration
    Args:
        config_path: Path to configuration file
    Returns:
        Dict containing book configuration
    Raises:
        FileNotFoundError: If config file missing
        yaml.YAMLError: If config is malformed
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Validate required configuration sections
    required_sections = ['title', 'authorship', 'template', 'style', 'build']
    missing = [section for section in required_sections if section not in config]
    if missing:
        raise ValueError(f"Missing required configuration sections: {', '.join(missing)}")
    
    return config

def load_metadata(metadata_path: Path) -> dict:
    """Load existing build metadata if present, or create new
    Args:
        metadata_path: Path to metadata file
    Returns:
        Dict containing current build metadata
    """
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError:
            # If metadata is corrupted, start fresh
            pass
    
    # Return empty metadata structure if no existing file or on error
    return {
        'last_build': None,
        'packages': [],
        'recipes': {},
        'sections': {}
    } 