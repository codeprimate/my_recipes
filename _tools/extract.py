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

    This class is part of the recipe book build pipeline, handling the second stage
    after initial directory scanning. It processes LaTeX recipe files marked as changed
    in the build metadata, extracting their content and requirements.

    Key Features:
    - Extracts content between \\begin{document} and \\end{document} tags
    - Identifies LaTeX package requirements from \\usepackage statements
    - Extracts recipe titles from \\title{} commands
    - Maintains build directory structure for extracted content
    - Updates metadata with extraction results and package requirements
    - Tracks extraction errors for debugging
    - Provides incremental processing (only changed files)

    Build Pipeline Role:
    - Reads metadata from scan.py results
    - Processes files marked as changed
    - Saves extracted content to _build/bodies/
    - Updates metadata.yml with extraction results
    - Prepares content for preprocessing stage

    Metadata Updates:
    - Per recipe:
        - Required packages list
        - Extracted content path
        - Recipe title
        - Processing status
    - Global:
        - Consolidated package requirements
        - Extraction errors
        - Build state tracking

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

    def extract_content(self, recipe_path: Path) -> Tuple[str, Set[str], Optional[str]]:
        """Extract content and package requirements from a LaTeX recipe file.

        Args:
            recipe_path: Path to LaTeX recipe file to process

        Returns:
            tuple: (content, packages, title) where:
                - content (str): Extracted content between document tags
                - packages (Set[str]): Set of required LaTeX package names
                - title (Optional[str]): Title from \title{} command if found
        """
        packages = set()
        content = ""
        title = None
        
        with open(recipe_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        in_document = False
        for line in lines:
            # Look for package requirements
            if r'\usepackage' in line:
                package = line.split('{')[1].split('}')[0]
                packages.add(package)
            
            # Look for title
            if r'\title{' in line:
                title = line.split(r'\title{')[1].split('}')[0]
            
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
            
        return content.strip(), packages, title

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
        # Convert the entire path at once, before creating any directories
        safe_path = Path(*[part.replace(' ', '_') for part in recipe_path.parts])
        build_path = self.bodies_dir / safe_path
        
        # Create only the necessary parent directories
        build_path.parent.mkdir(parents=True, exist_ok=True)

        # Save content to file
        with open(build_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Return path relative to build directory
        return build_path.relative_to(self.build_dir)

    def update_metadata(self, recipe_path: str, packages: Set[str], extracted_path: Path, title: Optional[str]) -> None:
        """Update metadata with extraction results.

        Args:
            recipe_path: Path to original recipe file
            packages: Set of required LaTeX packages
            extracted_path: Path where extracted content was saved
            title: Recipe title if found in LaTeX file
        """
        if recipe_path not in self.metadata['recipes']:
            print(f"Error: Recipe {recipe_path} not found in metadata", file=sys.stderr)
            return
        
        update_data = {
            'packages': list(packages),
            'extracted_body': str(extracted_path) if extracted_path else None
        }
        
        if title:
            update_data['title'] = title
        
        self.metadata['recipes'][recipe_path].update(update_data)
        
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

        Iterates through recipes in metadata and processes those marked as changed:
        - Extracts content and package requirements from LaTeX files
        - Saves extracted content to build directory
        - Updates metadata with extraction results
        - Tracks any errors encountered during processing

        Only processes recipes where metadata['recipes'][path]['changed'] is True.
        This allows for incremental builds that only process modified files.

        Returns:
            Dict[str, any]: Updated metadata dictionary containing:
                - Extracted content paths
                - Package requirements
                - Recipe titles
                - Any extraction errors encountered
        """
        for recipe_path, recipe_data in self.metadata['recipes'].items():
            # Only process if explicitly marked as changed
            if recipe_data.get('changed', False):
                try:
                    content, packages, title = self.extract_content(Path(recipe_path))
                    extracted_path = self.save_extracted_content(Path(recipe_path), content)
                    self.update_metadata(recipe_path, packages, extracted_path, title)
                    
                except Exception as e:
                    self.errors.append({
                        'recipe': recipe_path,
                        'error': str(e),
                        'type': type(e).__name__
                    })
                    print(f"Error processing {recipe_path}: {e}", file=sys.stderr)

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