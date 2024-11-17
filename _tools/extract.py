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
    """Extracts content and package requirements from LaTeX recipe files.

    This class handles the extraction of content between document tags and identifies
    required LaTeX packages from recipe source files. It maintains a build directory
    structure and updates metadata to track extraction status.

    Key Features:
    - Extracts content between begin{document} and end{document}
    - Identifies LaTeX package requirements from usepackage statements
    - Maintains build directory structure for extracted content
    - Updates metadata with extraction results and package requirements
    - Tracks extraction errors for debugging

    Attributes:
        config_path (Path): Path to book configuration file
        build_dir (Path): Path to build output directory
        metadata_path (Path): Path to build metadata file
        bodies_dir (Path): Path to extracted content directory
        config (dict): Loaded configuration settings
        metadata (dict): Build metadata tracking
        errors (list): List of extraction errors encountered
    """

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
        """Extract content and package requirements from a LaTeX recipe file.

        Processes a recipe file to extract:
        1. Content between begin{document} and end{document} tags
        2. Package requirements from usepackage statements

        Args:
            recipe_path: Path to LaTeX recipe file to process

        Returns:
            tuple: (content, packages) where:
                - content (str): Extracted content between document tags
                - packages (Set[str]): Set of required LaTeX package names

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
            recipe_path: Original recipe file path (used for directory structure)
            content: Extracted LaTeX content to save

        Returns:
            Path: Location where content was saved, relative to build directory

        Raises:
            OSError: If unable to create directories or write file
        """
        # Create corresponding path in build directory
        relative_path = Path(recipe_path)
        
        # Replace spaces with underscores in the path components
        path_parts = [part.replace(' ', '_') for part in relative_path.parts]
        safe_path = Path(*path_parts)
        
        build_path = self.bodies_dir / safe_path

        # Create parent directories if they don't exist
        build_path.parent.mkdir(parents=True, exist_ok=True)

        # Save content to file
        with open(build_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Return path relative to build directory
        return build_path.relative_to(self.build_dir)

    def update_metadata(self, recipe_path: str, packages: Set[str], extracted_path: Path) -> None:
        """Update metadata with extraction results.

        Updates the build metadata with:
        - Package requirements for the recipe
        - Path to extracted content file
        - Global consolidated package list

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

        Iterates through recipes in metadata and:
        1. Checks if extraction is needed based on change status
        2. Extracts content and identifies packages
        3. Saves extracted content
        4. Updates metadata
        5. Tracks any errors encountered

        Returns:
            Dict containing updated build metadata including:
                - Recipe extraction status
                - Package requirements
                - Extraction errors

        Note:
            Continues processing remaining recipes if an error occurs with one recipe.
            All errors are collected in self.errors list.
        """
        for recipe_path, recipe_data in self.metadata['recipes'].items():
            # Check if extraction is needed
            needs_extraction = (
                recipe_data.get('changed', False) or  # Extract if changed
                'extracted_body' not in recipe_data or  # Never extracted
                not recipe_data.get('extracted_body') or  # Empty path
                not (self.build_dir / recipe_data.get('extracted_body', '')).exists()  # File missing
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
        
        print("Extracting recipe content...")
        metadata = extractor.extract_all()
        print_extraction_summary(metadata)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 