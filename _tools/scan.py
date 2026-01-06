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
    packages:
        - tocloft
        - geometry
        - fontspec
        - multicol
    recipes:
        "desserts/chocolate_cake.tex":
            section: "desserts"
            mtime: "2024-03-15T10:20:00Z"
            title: "Chocolate Cake"
            packages:
                - tocloft
                - fontspec
            extracted_body: "_build/bodies/desserts/chocolate_cake.tex"
            preprocessed: false
            changed: false
    sections:
        "desserts": "Desserts"
        "entrees": "Entrees"
"""

import os
import sys
import yaml
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from helpers import load_config, load_metadata
from rich.console import Console
from rich.table import Table

class RecipeScanner:
    """Handles recipe book content scanning and metadata generation
    
    The scanner performs these key steps:
    1. Discovers content directories (sections)
    2. Scans for recipe files within sections
    3. Detects changes from previous build
    4. Updates build metadata
    
    Error Handling:
    - All errors are collected in self.errors list
    - Each error includes section, error message, and error type
    - Scanning continues even if errors occur
    """

    def __init__(self, config_path: str = "_tools/book.yml"):
        """Initialize scanner with configuration
        Args:
            config_path: Path to book.yml configuration (relative to project root)
        """
        self.errors = []
        self.config_path = Path(config_path)
        self.config = load_config(self.config_path)
        self.build_dir = Path(self.config['build']['output_dir'])
        self.build_dir.mkdir(exist_ok=True)
        self.metadata_path = self.build_dir / "metadata.yml"
        self.console = Console()

    def scan_content_directories(self) -> Dict[str, str]:
        """Scan for content directories and process section names
        
        Discovers directories that:
        - Are not hidden (don't start with '.')
        - Are not system directories (don't start with '_')
        - Exist in the project root
        
        Returns:
            Dict[str, str]: Mapping of directory paths to formatted section titles
            
        Example:
            "01-appetizers" -> "Appetizers"
            "main_dishes" -> "Main Dishes"
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
            Formatted section title (without numeric prefix)
        """
        # Remove numeric prefix if present (e.g., "01-", "01 ")
        # Match leading digits followed by dash or space
        name = re.sub(r'^\d+\s*[-]?\s*', '', directory)
        
        # Replace underscores/hyphens with spaces
        name = name.replace('-', ' ').replace('_', ' ')
        
        # Strip and capitalize words
        return name.strip().title()

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
        """Compare current scan against previous build to detect changes.
        
        For unchanged files: preserves ALL existing metadata (title, extracted_body, 
        packages, preprocessed, etc.) to avoid losing build state.
        
        For changed/new files: uses fresh scan data with reset build state.
        """
        updated = {}
        existing_recipes = existing_metadata.get('recipes', {})
        
        for path, metadata in new_files.items():
            if path in existing_recipes:
                old_mtime = datetime.fromisoformat(existing_recipes[path].get('mtime', ''))
                new_mtime = datetime.fromisoformat(metadata.get('mtime', ''))
                changed = old_mtime != new_mtime
                
                if not changed:
                    # Unchanged: keep ALL existing metadata, just update changed flag
                    updated[path] = existing_recipes[path].copy()
                    updated[path]['changed'] = False
                else:
                    # Changed: use fresh scan data, reset build state
                    updated[path] = metadata.copy()
                    updated[path]['changed'] = True
                    updated[path]['preprocessed'] = False
            else:
                # New file: use scan data, mark as changed
                updated[path] = metadata.copy()
                updated[path]['changed'] = True
        
        return updated

    def update_metadata(self, sections: Dict[str, str], recipes: Dict[str, dict]) -> dict:
        """Update and save build metadata
        
        Updates:
        - Section directory mapping
        - Recipe metadata
        - Last build timestamp
        - Error tracking
        
        Args:
            sections: Section directory mapping
            recipes: Recipe metadata
            
        Returns:
            dict: Complete updated metadata
            
        Side Effects:
            Writes updated metadata to self.metadata_path
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
        
        self.console.print("\n[bold cyan]╔══ Content Scanning ══╗[/bold cyan]")
        
        try:
            with self.console.status("[yellow]Scanning content directories...", spinner="dots") as status:
                sections = self.scan_content_directories()
                self.console.print(f"[green]✓ Found {len(sections)} sections[/green]")
                
                status.update("[yellow]Scanning for recipe files...")
                recipes = self.scan_recipe_files(sections)
                self.console.print(f"[green]✓ Found {len(recipes)} recipes[/green]")
                
                status.update("[yellow]Detecting changes...")
                existing = load_metadata(self.metadata_path)
                recipes = self.detect_changes(existing, recipes)
                changed_count = sum(1 for r in recipes.values() if r.get('changed', False))
                self.console.print(f"[green]✓ Detected {changed_count} changed recipes[/green]")
                
                status.update("[yellow]Updating build metadata...")
                metadata = self.update_metadata(sections, recipes)
                self.console.print("[green]✓ Build metadata updated[/green]")
                
        except Exception as e:
            self.console.print(f"[red]✗ Error during scanning: {str(e)}[/red]")
            self.errors.append({
                'section': 'scanning',
                'error': str(e),
                'type': type(e).__name__
            })
            
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
        scanner = RecipeScanner(config_path=args.config)
        metadata = scanner.scan()
        
        # Add a separator before the summary
        scanner.console.print("\n[bold cyan]╔══ Scan Summary ══╗[/bold cyan]")
        print_scan_summary(metadata)
        
        if scanner.errors:
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
