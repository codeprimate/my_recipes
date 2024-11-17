"""Shared helper functions for recipe book tools

This module provides common functionality used across the build system:
- Configuration loading and validation
- Build metadata management
- Error handling utilities

Key Components:
- load_config: Loads and validates book configuration
- load_metadata: Manages build state tracking

Developer Notes:
- Configuration must include all required sections
- Metadata maintains incremental build state
- All file operations use UTF-8 encoding
"""

import yaml
from pathlib import Path
from typing import Dict, List

def load_config(config_path: Path) -> dict:
    """Load and validate book configuration
    
    The configuration file must contain these required sections:
    - title: Book title information
    - authorship: Author and copyright details
    - template: Template file to use
    - style: Book styling settings
    - build: Build process configuration
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Dict containing validated book configuration. Example:
        {
            'title': {
                'name': 'Family Cookbook',
                'subtitle': 'Collected Recipes'
            },
            'authorship': {
                'author': 'Jane Smith',
                'copyright': '2024'
            },
            'template': 'book.tex.jinja',
            'style': {
                'documentclass': 'article',
                'font_size': '11pt',
                'include_toc': True
            },
            'build': {
                'output_dir': '_build'
            }
        }
    
    Raises:
        FileNotFoundError: If config file missing
        yaml.YAMLError: If config is malformed
        ValueError: If required sections are missing
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
    
    The metadata file tracks:
    - Last build timestamp
    - Required LaTeX packages
    - Recipe processing state
    - Section organization
    
    Args:
        metadata_path: Path to metadata file
    
    Returns:
        Dict containing current build metadata with structure:
        {
            'last_build': datetime or None,
            'packages': List[str],
            'recipes': Dict[str, Dict],
            'sections': Dict[str, str]
        }
    
    Note:
        Returns empty metadata structure if file missing or corrupted
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