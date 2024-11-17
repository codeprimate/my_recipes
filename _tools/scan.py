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
from helpers import load_config, load_metadata
from rich.console import Console
from rich.table import Table

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
        self.config = load_config(self.config_path)
        
        # Create build directory if it doesn't exist
        self.build_dir.mkdir(exist_ok=True)
        
        self.errors = []  # Add error tracking

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
        metadata = load_metadata(self.metadata_path)
        
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
        sections = {}
        recipes = {}
        
        try:
            sections = self.scan_content_directories()
        except Exception as e:
            self.errors.append({
                'section': 'directory_scan',
                'error': str(e),
                'type': type(e).__name__
            })
        
        try:
            recipes = self.scan_recipe_files(sections)
        except Exception as e:
            self.errors.append({
                'section': 'recipe_scan',
                'error': str(e),
                'type': type(e).__name__
            })
        
        existing = load_metadata(self.metadata_path)
        recipes = self.detect_changes(existing, recipes)
        
        metadata = self.update_metadata(sections, recipes)
        metadata['scan_errors'] = self.errors
        return metadata


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


def print_scan_summary(metadata: dict) -> None:
    """Print summary of scan results using rich formatting
    Args:
        metadata: Build metadata dictionary
    """
    console = Console()
    
    # Print summary statistics
    total_recipes = len(metadata['recipes'])
    total_sections = len(metadata['sections'])
    error_count = len(metadata.get('scan_errors', []))
    changed_count = sum(1 for r in metadata['recipes'].values() if r.get('changed', False))
    
    console.print("\n[bold]Scan Summary:[/bold]")
    console.print(f"• Total sections: {total_sections}")
    console.print(f"• Total recipes: {total_recipes}")
    console.print(f"• Changed recipes: [yellow]{changed_count}[/yellow]")
    console.print(f"• Errors encountered: [red]{error_count}[/red]\n")

    # Create sections table
    section_table = Table(title="Sections Detected")
    section_table.add_column("Directory", style="cyan")
    section_table.add_column("Title")
    
    for directory, title in metadata['sections'].items():
        section_table.add_row(directory, title)
    
    console.print(section_table)
    
    # Create recipes table
    recipe_table = Table(title="\nRecipes Found")
    recipe_table.add_column("Recipe", style="cyan")
    recipe_table.add_column("Section")
    recipe_table.add_column("Status", justify="center")
    
    for recipe_path, recipe_data in metadata['recipes'].items():
        status = "[yellow]Changed[/yellow]" if recipe_data.get('changed', False) else "[green]Unchanged[/green]"
        recipe_table.add_row(recipe_path, recipe_data['section'], status)
    
    console.print(recipe_table)
    
    # Print errors table if any exist
    if error_count > 0:
        error_table = Table(title="\nErrors Encountered")
        error_table.add_column("Section", style="cyan")
        error_table.add_column("Error Type", style="magenta")
        error_table.add_column("Message", style="red")
        
        for error in metadata['scan_errors']:
            error_table.add_row(
                error['section'],
                error['type'],
                error['error']
            )
        
        console.print(error_table)

def main():
    """Main entry point when run as script"""
    args = parse_args()
    
    try:
        scanner = RecipeScanner(
            config_path=args.config,
            build_dir=args.build_dir
        )
        
        metadata = scanner.scan()
        print_scan_summary(metadata)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
