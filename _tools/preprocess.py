#!/usr/bin/env python3

"""Recipe Book Content Preprocessor

This module normalizes and prepares extracted LaTeX content for final book compilation.
It performs multiple preprocessing steps to ensure consistency across all recipes.

Usage as module:
    from _tools.preprocess import RecipePreprocessor
    
    preprocessor = RecipePreprocessor()
    metadata = preprocessor.process_all()

Usage from command line:
    python _tools/preprocess.py [--config path/to/config] [--build-dir path/to/build]
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from helpers import load_config, load_metadata
from rich.console import Console
from rich.table import Table

class RecipePreprocessor:
    def __init__(self, config_path: str = "_tools/book.yml", build_dir: str = "_build"):
        """Initialize preprocessor with configuration
        
        Args:
            config_path: Path to book.yml configuration
            build_dir: Path to build directory
        """
        self.config_path = Path(config_path)
        self.build_dir = Path(build_dir)
        self.metadata_path = self.build_dir / "metadata.yml"
        self.bodies_dir = self.build_dir / "bodies"
        
        # Load config and metadata
        self.config = load_config(self.config_path)
        self.metadata = load_metadata(self.metadata_path)
        
        self.errors = []
        self.console = Console()

    def remove_layout_commands(self, content: str) -> str:
        """Remove layout-affecting commands that are handled by the master template"""
        # Lines to filter out
        filtered_lines = [
            r'\maketitle',
            r'\thispagestyle{empty}',
        ]
        
        # Split content into lines, filter, and rejoin
        lines = content.splitlines()
        cleaned_lines = [line for line in lines 
                        if not any(cmd in line for cmd in filtered_lines)]
        return '\n'.join(cleaned_lines)

    def action_2(self, content: str) -> str:
        """Second preprocessing action"""
        return content

    def action_3(self, content: str) -> str:
        """Third preprocessing action"""
        return content

    def process_recipe(self, recipe_path: str, recipe_data: dict) -> bool:
        """Process a single recipe through all preprocessing steps
        
        Args:
            recipe_path: Path to recipe file
            recipe_data: Recipe metadata
            
        Returns:
            bool: True if processing successful
        """
        try:
            # Load extracted content - convert relative path to absolute
            content_path = self.build_dir / recipe_data['extracted_body']
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Apply preprocessing steps
            content = self.remove_layout_commands(content)
            content = self.action_2(content)
            content = self.action_3(content)

            # Save processed content back to same location
            with open(content_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Update metadata
            recipe_data['preprocessed'] = True
            return True

        except Exception as e:
            self.errors.append({
                'recipe': recipe_path,
                'error': str(e),
                'type': type(e).__name__
            })
            return False

    def process_all(self) -> dict:
        """Process all recipes that need preprocessing"""
        self.console.print("\n[bold cyan]╔══ Recipe Preprocessing ══╗[/bold cyan]")
        
        # Calculate statistics
        total_recipes = len(self.metadata['recipes'])
        needs_processing = sum(1 for r in self.metadata['recipes'].values() 
                              if not r.get('preprocessed', False))
        processed = 0
        
        with self.console.status("[yellow]Processing recipes...", spinner="dots") as status:
            for recipe_path, recipe_data in self.metadata['recipes'].items():
                if not recipe_data.get('preprocessed', False):
                    try:
                        status.update(f"[yellow]Processing: {recipe_path}")
                        if self.process_recipe(recipe_path, recipe_data):
                            processed += 1
                            self.console.print(f"[green]✓ Processed:[/green] {recipe_path}")
                        else:
                            self.console.print(f"[red]✗ Failed:[/red] {recipe_path}")
                    except Exception as e:
                        self.errors.append({
                            'recipe': recipe_path,
                            'error': str(e),
                            'type': type(e).__name__
                        })
                        self.console.print(f"[red]✗ Failed:[/red] {recipe_path} ({type(e).__name__})")

        # Update metadata with errors
        self.metadata['preprocessing_errors'] = self.errors
        
        # Save updated metadata
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            import yaml
            yaml.safe_dump(self.metadata, f, sort_keys=False)

        return self.metadata


def parse_args():
    """Parse command line arguments"""
    import argparse
    parser = argparse.ArgumentParser(description="Recipe Content Preprocessor")
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


def print_preprocessing_summary(metadata: dict) -> None:
    """Print summary of preprocessing results using rich formatting
    
    Args:
        metadata: Build metadata dictionary
    """
    console = Console()
    
    # Calculate statistics
    total_recipes = len(metadata['recipes'])
    needs_processing = sum(1 for r in metadata['recipes'].values() 
                          if not r.get('preprocessed', False))
    processed_count = sum(1 for r in metadata['recipes'].values() 
                         if r.get('preprocessed'))
    error_count = len(metadata.get('preprocessing_errors', []))
    
    console.print("\n[bold]Preprocessing Summary:[/bold]")
    console.print(f"• Total recipes: {total_recipes}")
    console.print(f"• Needs processing: {needs_processing}")
    console.print(f"• Successfully processed: [green]{processed_count}[/green]")
    console.print(f"• Failed: [red]{error_count}[/red]\n")

    if needs_processing > 0:
        # Create recipes table
        recipe_table = Table(title="Processing Status")
        recipe_table.add_column("Recipe", style="cyan")
        recipe_table.add_column("Section")
        recipe_table.add_column("Status", justify="center")
        
        for recipe_path, recipe_data in metadata['recipes'].items():
            if not recipe_data.get('preprocessed', False):
                status = "[green]✓ Processed[/green]" if recipe_data.get('preprocessed') else "[red]✗ Failed[/red]"
                recipe_table.add_row(
                    recipe_path,
                    recipe_data['section'],
                    status
                )
        
        console.print(recipe_table)
    
    # Print errors table if any exist
    if error_count > 0:
        error_table = Table(title="\nErrors Encountered")
        error_table.add_column("Recipe", style="cyan")
        error_table.add_column("Error Type", style="magenta")
        error_table.add_column("Message", style="red")
        
        for error in metadata['preprocessing_errors']:
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
        console = Console()
        with console.status("[yellow]Initializing preprocessor...", spinner="dots"):
            preprocessor = RecipePreprocessor(
                config_path=args.config,
                build_dir=args.build_dir
            )
        
        metadata = preprocessor.process_all()
        print_preprocessing_summary(metadata)
        
    except Exception as e:
        console = Console(stderr=True)
        console.print(f"[red]Error: {e}[/red]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 