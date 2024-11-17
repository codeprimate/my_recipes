#!/usr/bin/env python3

"""Recipe Book Scanner

This module scans a directory structure for LaTeX recipe files and generates build metadata.

Usage as module:
    from _tools.scan import RecipeScanner
    
    # Using defaults (_tools/book.yml config, _build directory)
    scanner = RecipeScanner()
    metadata = scanner.scan()
    
    # With custom paths
    scanner = RecipeScanner(config_path="custom/config.yml", build_dir="custom/build")
    metadata = scanner.scan()

Usage from command line:
    # Using defaults
    python _tools/scan.py
    
    # With custom paths
    python _tools/scan.py --config custom/config.yml --build-dir custom/build
    
    # Show help
    python _tools/scan.py --help

Returns:
    When run as script: Creates/updates _build/metadata.yml
    When used as module: Returns metadata dict

Example metadata.yml structure:
    last_build: "2024-03-16T15:30:00Z"
    recipes:
        "appetizers/bruschetta.tex":
            section: "appetizers"
            mtime: "2024-03-15T10:20:00Z"
            title: "Bruschetta"
            preprocessed: false
    sections:
        "appetizers": "Appetizers"
        "main-dishes": "Main Dishes"
"""

import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class RecipeScanner:
    def __init__(self, config_path: str = "book.yml", build_dir: str = "_build"):
        """Initialize scanner with configuration
        Args:
            config_path: Path to book.yml configuration (relative to project root)
            build_dir: Path to build directory (relative to project root)
        """
        self.config_path = Path(config_path)
        self.build_dir = Path(build_dir)
        self.metadata_path = self.build_dir / "metadata.yml"
        
        # Load and store configuration
        self.config = self.load_config(self.config_path)
        
        # Create build directory if it doesn't exist
        self.build_dir.mkdir(exist_ok=True)

    def load_config(self, config_path: str) -> dict:
        """Load and validate book configuration
        Returns:
            Dict containing book configuration
        Raises:
            FileNotFoundError: If config file missing
            yaml.YAMLError: If config is malformed
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # Validate required fields
            required_fields = ['title', 'authorship', 'template', 'style', 'build']
            missing = [field for field in required_fields if field not in config]
            if missing:
                raise ValueError(f"Missing required config fields: {', '.join(missing)}")
                
            return config
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing configuration: {e}")

    def load_metadata(self) -> dict:
        """Load existing build metadata if present, or create new
        Returns:
            Dict containing current build metadata
        """
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
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

    def scan_content_directories(self) -> Dict[str, str]:
        """Scan for content directories, excluding system dirs
        Returns:
            Dict mapping directory paths to processed section names
        """
        sections = {}
        content_dir = Path('.')  # Start from current directory
        
        for item in content_dir.iterdir():
            # Skip hidden and system directories
            if item.name.startswith('_') or item.name.startswith('.'):
                continue
            
            if item.is_dir():
                sections[item.name] = self.process_section_name(item.name)
        
        return sections

    def process_section_name(self, directory: str) -> str:
        """Convert directory name to formatted section title
        Args:
            directory: Raw directory name
        Returns:
            Formatted section title
        """
        # Remove numeric prefix if present (e.g., "01-")
        name = directory.split('-', 1)[-1] if '-' in directory else directory
        
        # Replace underscores/hyphens with spaces
        name = name.replace('-', ' ').replace('_', ' ')
        
        # Capitalize words
        return name.title()

    def scan_recipe_files(self, section_dirs: Dict[str, str]) -> Dict[str, dict]:
        """Scan sections for recipe files
        Args:
            section_dirs: Mapping of directory paths to section names
        Returns:
            Dict of recipe metadata keyed by file path
        """
        recipes = {}
        
        for section_dir in section_dirs:
            section_path = Path(section_dir)
            if not section_path.is_dir():
                continue
            
            for recipe_file in section_path.glob('*.tex'):
                relative_path = str(recipe_file.relative_to('.'))
                recipes[relative_path] = {
                    'section': section_dir,
                    'mtime': datetime.fromtimestamp(recipe_file.stat().st_mtime).isoformat(),
                    'title': recipe_file.stem.replace('_', ' ').title(),
                    'packages': [],
                    'extracted_body': False,
                    'preprocessed': False
                }
        
        return recipes

    def detect_changes(self, existing_metadata: dict, new_files: Dict[str, dict]) -> Dict[str, dict]:
        """Compare against previous build to detect changes
        Args:
            existing_metadata: Previous build metadata
            new_files: Newly scanned files
        Returns:
            Updated recipe metadata with change flags
        """
        updated = {}
        existing_recipes = existing_metadata.get('recipes', {})
        
        for path, metadata in new_files.items():
            updated[path] = metadata.copy()
            
            # Check if file existed in previous build
            if path in existing_recipes:
                old_mtime = existing_recipes[path].get('mtime')
                new_mtime = metadata.get('mtime')
                updated[path]['changed'] = old_mtime != new_mtime
            else:
                # New file, mark as changed
                updated[path]['changed'] = True
            
        return updated

    def update_metadata(self, sections: Dict[str, str], recipes: Dict[str, dict]) -> dict:
        """Update and save build metadata
        Args:
            sections: Section directory mapping
            recipes: Recipe metadata
        Returns:
            Complete updated metadata
        """
        metadata = self.load_metadata()
        
        # Update sections and recipes
        metadata['sections'] = sections
        metadata['recipes'] = recipes
        metadata['last_build'] = datetime.now().isoformat()
        
        # Save updated metadata
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, default_flow_style=False)
        
        return metadata

    def scan(self) -> dict:
        """Execute full scanning process
        Returns:
            Updated build metadata
        """
        # Scan for content directories
        sections = self.scan_content_directories()
        
        # Scan for recipe files
        recipes = self.scan_recipe_files(sections)
        
        # Load existing metadata and detect changes
        existing = self.load_metadata()
        recipes = self.detect_changes(existing, recipes)
        
        # Update and save metadata
        return self.update_metadata(sections, recipes)


def parse_args():
    """Parse command line arguments
    Returns:
        Namespace containing parsed arguments
    """
    import argparse
    parser = argparse.ArgumentParser(description="Recipe Book Scanner")
    parser.add_argument(
        "--config",
        default="_tools/book.yml",
        help="Path to configuration file (default: _tools/book.yml)"
    )
    parser.add_argument(
        "--build-dir",
        default="_build",
        help="Build directory path (default: _build)"
    )
    return parser.parse_args()


def main():
    """Main entry point when run as script"""
    args = parse_args()
    
    try:
        # Initialize scanner with command line arguments
        scanner = RecipeScanner(
            config_path=args.config,
            build_dir=args.build_dir
        )
        
        # Execute scan and get metadata
        metadata = scanner.scan()
        
        # Print summary
        print(f"Scan complete:")
        print(f"- {len(metadata['sections'])} sections detected")
        print(f"- {len(metadata['recipes'])} recipes found")
        print(f"- Metadata written to {scanner.metadata_path}")
        
    except (FileNotFoundError, yaml.YAMLError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
