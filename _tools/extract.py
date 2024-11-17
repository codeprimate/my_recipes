#!/usr/bin/env python3

"""Recipe Book Content Extractor

This module extracts content and package requirements from LaTeX recipe files.

Usage as module:
    from _tools.extract import RecipeExtractor
    
    extractor = RecipeExtractor()
    metadata = extractor.extract_all()

Usage from command line:
    python _tools/extract.py [--config path/to/config] [--build-dir path/to/build]
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from helpers import load_config, load_metadata
from rich.console import Console
from rich.table import Table


class RecipeExtractor:
    def __init__(self, config_path: str = "_tools/book.yml", build_dir: str = "_build") -> None:
        """Initialize extractor with configuration.

        Args:
            config_path: Path to book.yml configuration file
            build_dir: Path to build directory for extracted content

        Raises:
            FileNotFoundError: If config file cannot be found
            yaml.YAMLError: If config file is invalid
        """
        self.config_path = Path(config_path)
        self.build_dir = Path(build_dir)
        self.metadata_path = self.build_dir / "metadata.yml"
        self.bodies_dir = self.build_dir / "bodies"
        
        # Create build directories if they don't exist
        self.bodies_dir.mkdir(parents=True, exist_ok=True)
        
        # Load config and metadata
        self.config = load_config(self.config_path)
        self.metadata = load_metadata(self.metadata_path)
        
        # Ensure build output directory matches instance setting
        self.config['build']['output_dir'] = str(self.build_dir)
        self.errors = []

    def extract_content(self, recipe_path: Path) -> Tuple[str, Set[str]]:
        """Extract content and package requirements from a recipe file.

        Args:
            recipe_path: Path to LaTeX recipe file to process

        Returns:
            Tuple containing:
                - str: Extracted content between document tags
                - Set[str]: Set of required LaTeX package names

        Raises:
            ValueError: If no content found between document tags
            FileNotFoundError: If recipe file cannot be opened
        """
        packages = set()
        content = ""
        
        with open(recipe_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        in_document = False
        for line in lines:
            # Look for package requirements
            if r'\usepackage' in line:
                # Extract package name from \usepackage{package_name}
                package = line.split('{')[1].split('}')[0]
                packages.add(package)
                
            # Track document content
            if r'\begin{document}' in line:
                in_document = True
                continue
            elif r'\end{document}' in line:
                in_document = False
                continue
                
            # Collect content between document tags
            if in_document:
                content += line
                
        if not content:
            raise ValueError(f"No content found between document tags in {recipe_path}")
            
        return content.strip(), packages

    def save_extracted_content(self, recipe_path: Path, content: str) -> Path:
        """Save extracted content to build directory.

        Args:
            recipe_path: Original recipe file path
            content: Extracted LaTeX content to save

        Returns:
            Path: Location where content was saved in build directory

        Raises:
            OSError: If unable to create directories or write file
        """
        # Create corresponding path in build directory
        relative_path = Path(recipe_path)
        build_path = self.bodies_dir / relative_path

        # Create parent directories if they don't exist
        build_path.parent.mkdir(parents=True, exist_ok=True)

        # Save content to file
        with open(build_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return build_path

    def update_metadata(self, recipe_path: str, packages: Set[str], extracted_path: Path) -> None:
        """Update metadata with extraction results.

        Args:
            recipe_path: Path to original recipe file
            packages: Set of required LaTeX packages
            extracted_path: Path where extracted content was saved

        Raises:
            yaml.YAMLError: If metadata cannot be saved
        """
        # Update recipe entry
        if recipe_path not in self.metadata['recipes']:
            print(f"Error: Recipe {recipe_path} not found in metadata", file=sys.stderr)
            return
        
        self.metadata['recipes'][recipe_path].update({
            'packages': list(packages),
            'extracted_body': str(extracted_path)
        })
        
        # Update global package list
        if 'packages' not in self.metadata:
            self.metadata['packages'] = []
        self.metadata['packages'] = list(set(self.metadata['packages']).union(packages))
        
        # Save updated metadata
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            import yaml
            yaml.safe_dump(self.metadata, f, sort_keys=False)

    def extract_all(self) -> Dict[str, any]:
        """Process all recipes that need extraction.

        Returns:
            Dict containing updated build metadata and list of errors

        Raises:
            Exception: Only if critical errors occur (config/metadata related)
        """
        for recipe_path, recipe_data in self.metadata['recipes'].items():
            # Check if extraction is needed
            needs_extraction = (
                recipe_data.get('changed', False) and  # Only extract if changed is true
                (
                    'extracted_body' not in recipe_data or  # Never extracted
                    not recipe_data['extracted_body'] or    # Empty path
                    not Path(recipe_data['extracted_body']).exists()  # File missing
                )
            )

            if needs_extraction:
                try:
                    content, packages = self.extract_content(Path(recipe_path))
                    extracted_path = self.save_extracted_content(Path(recipe_path), content)
                    self.update_metadata(recipe_path, packages, extracted_path)
                    
                except Exception as e:
                    self.errors.append({
                        'recipe': recipe_path,
                        'error': str(e),
                        'type': type(e).__name__
                    })
                    print(f"Error processing {recipe_path}: {e}", file=sys.stderr)
                    # Continue processing other recipes instead of raising

        # Add errors to metadata
        self.metadata['extraction_errors'] = self.errors
        return self.metadata


def parse_args():
    """Parse command line arguments"""
    import argparse
    parser = argparse.ArgumentParser(description="Recipe Content Extractor")
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


def print_extraction_summary(metadata: dict) -> None:
    """Print summary of extraction results using rich formatting
    Args:
        metadata: Build metadata dictionary
    """
    console = Console()
    
    # Print summary statistics
    total_recipes = len(metadata['recipes'])
    error_count = len(metadata.get('extraction_errors', []))
    success_count = sum(1 for r in metadata['recipes'].values() if r.get('extracted_body'))
    
    console.print("\n[bold]Extraction Summary:[/bold]")
    console.print(f"• Total recipes: {total_recipes}")
    console.print(f"• Successfully processed: [green]{success_count}[/green]")
    console.print(f"• Failed: [red]{error_count}[/red]\n")

    # Create recipes table
    recipe_table = Table(title="Recipes Processed")
    recipe_table.add_column("Recipe", style="cyan")
    recipe_table.add_column("Section")
    recipe_table.add_column("Status", justify="center")
    
    for recipe_path, recipe_data in metadata['recipes'].items():
        status = "[green]Extracted[/green]" if recipe_data.get('extracted_body') else "[yellow]Skipped[/yellow]"
        recipe_table.add_row(recipe_path, recipe_data['section'], status)
    
    console.print(recipe_table)
    
    # Print errors table if any exist
    if error_count > 0:
        error_table = Table(title="\nErrors Encountered")
        error_table.add_column("Recipe", style="cyan")
        error_table.add_column("Error Type", style="magenta")
        error_table.add_column("Message", style="red")
        
        for error in metadata['extraction_errors']:
            error_table.add_row(
                error['recipe'],
                error['type'],
                error['error']
            )
        
        console.print(error_table)

def main():
    """Main entry point when run as script"""
    args = parse_args()
    
    try:
        extractor = RecipeExtractor(
            config_path=args.config,
            build_dir=args.build_dir
        )
        
        metadata = extractor.extract_all()
        print_extraction_summary(metadata)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 