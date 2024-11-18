#!/usr/bin/env python3

"""Recipe Book Build System

Main entry point for the recipe book build system. Orchestrates the entire build pipeline
by coordinating the scanning, extraction, preprocessing, and compilation stages.

Usage:
    python _tools/build.py [--config path/to/config] [--build-dir path/to/build]
"""

import sys
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table

from scan import RecipeScanner
from extract import RecipeExtractor
from preprocess import RecipePreprocessor
from compile import BookCompiler
from helpers import load_config

class RecipeBookBuilder:
    """Orchestrates the complete recipe book build process"""

    def __init__(self, config_path: str = "_tools/book.yml", build_dir: str = "_build"):
        """Initialize builder with configuration
        
        Args:
            config_path: Path to book.yml configuration
            build_dir: Path to build directory
        """
        # Convert string paths to Path objects
        self.config_path = Path(config_path).resolve()
        self.build_dir = Path(build_dir).resolve()
        print(f"Build directory: {self.build_dir}")
        self.console = Console()
        
        # Ensure config file exists
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        else:
            print(f"Config path: {self.config_path}")
        
        # Load configuration
        self.config = load_config(self.config_path)
        
        # Create build directory
        self.build_dir.mkdir(exist_ok=True)
        
        # Initialize pipeline components
        self.scanner = RecipeScanner(config_path)
        self.extractor = RecipeExtractor(config_path)
        self.preprocessor = RecipePreprocessor(config_path, str(self.build_dir))
        self.compiler = BookCompiler(Path(config_path))
        
        # Track build status
        self.errors = []
        self.start_time = None
        self.end_time = None
        self.stage_times = {}  # Add this to track stage durations

    def clean_build_dir(self) -> None:
        """Remove all contents of the build directory"""
        if self.build_dir.exists():
            self.console.print("\n[bold yellow]Cleaning build directory...[/bold yellow]")
            for item in self.build_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    import shutil
                    shutil.rmtree(item)
            self.console.print("[dim]Build directory cleaned[/dim]")

    def build(self, clean: bool = False) -> Optional[Path]:
        """Execute complete build pipeline
        
        Args:
            clean: If True, clean build directory before building
        
        Returns:
            Optional[Path]: Path to compiled PDF if successful, None if failed
            
        The build process follows these stages:
        1. Scan content directories
        2. Extract content from LaTeX files
        3. Preprocess content
        4. Compile final book
        
        Each stage is executed only if previous stages succeed.
        """
        if clean:
            self.clean_build_dir()
            
        self.start_time = datetime.now()
        pdf_path = None

        try:
            # Stage 1: Scan
            stage_start = datetime.now()
            self.console.print("\n[bold blue]Stage 1: Scanning content...[/bold blue]")
            metadata = self.scanner.scan()
            self.stage_times['scan'] = datetime.now() - stage_start
            self.console.print(f"[dim]Scan completed in {self.stage_times['scan'].total_seconds():.1f}s[/dim]")
            if self.scanner.errors:
                self.errors.extend([{'stage': 'scan', **e} for e in self.scanner.errors])
                return None

            # Stage 2: Extract
            stage_start = datetime.now()
            self.console.print("\n[bold blue]Stage 2: Extracting content...[/bold blue]")
            metadata = self.extractor.extract_all()
            self.stage_times['extract'] = datetime.now() - stage_start
            self.console.print(f"[dim]Extraction completed in {self.stage_times['extract'].total_seconds():.1f}s[/dim]")
            if self.extractor.errors:
                self.errors.extend([{'stage': 'extract', **e} for e in self.extractor.errors])
                return None

            # Stage 3: Preprocess
            stage_start = datetime.now()
            self.console.print("\n[bold blue]Stage 3: Preprocessing content...[/bold blue]")
            metadata = self.preprocessor.process_all()
            self.stage_times['preprocess'] = datetime.now() - stage_start
            self.console.print(f"[dim]Preprocessing completed in {self.stage_times['preprocess'].total_seconds():.1f}s[/dim]")
            if self.preprocessor.errors:
                self.errors.extend([{'stage': 'preprocess', **e} for e in self.preprocessor.errors])
                return None

            # Stage 4: Compile
            stage_start = datetime.now()
            self.console.print("\n[bold blue]Stage 4: Compiling book...[/bold blue]")
            pdf_path = self.compiler.compile()
            self.stage_times['compile'] = datetime.now() - stage_start
            self.console.print(f"[dim]Compilation completed in {self.stage_times['compile'].total_seconds():.1f}s[/dim]")
            if self.compiler.errors:
                self.errors.extend([{'stage': 'compile', **e} for e in self.compiler.errors])
                return None

        except Exception as e:
            self.errors.append({
                'stage': 'build',
                'error': str(e),
                'type': type(e).__name__
            })
            return None
            
        finally:
            self.end_time = datetime.now()
            self.print_build_summary(pdf_path)

        return pdf_path

    def print_build_summary(self, pdf_path: Optional[Path]) -> None:
        """Print comprehensive build summary
        
        Args:
            pdf_path: Path to compiled PDF if build succeeded
        """
        duration = self.end_time - self.start_time
        
        self.console.print("\n[bold]Build Summary[/bold]")
        self.console.print(f"Duration: {duration.total_seconds():.1f} seconds")
        
        if pdf_path:
            self.console.print(f"Output: [green]{pdf_path}[/green]")
        else:
            self.console.print("[red]Build failed[/red]")

        if self.errors:
            error_table = Table(title="\nBuild Errors")
            error_table.add_column("Stage", style="cyan")
            error_table.add_column("Type", style="magenta")
            error_table.add_column("Error", style="red", no_wrap=False)
            
            for error in self.errors:
                error_table.add_row(
                    error['stage'],
                    error.get('type', 'Unknown'),
                    error.get('error', 'Unknown error')
                )
            
            self.console.print(error_table)


def parse_args():
    """Parse command line arguments"""
    import argparse
    parser = argparse.ArgumentParser(description="Recipe Book Builder")
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
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build directory before building"
    )
    return parser.parse_args()


def main():
    """Command-line entry point"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    args = parse_args()
    
    try:
        builder = RecipeBookBuilder(
            config_path=args.config,
            build_dir=args.build_dir
        )
        
        pdf_path = builder.build(clean=args.clean)
        
        # Set exit code based on build success
        sys.exit(0 if pdf_path else 1)
        
    except Exception as e:
        logging.error(f"Build failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 