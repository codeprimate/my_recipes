"""Recipe book compilation module

This module handles the final assembly and compilation of the recipe book,
including template rendering and LaTeX compilation.

Key Components:
- BookCompiler: Main class handling template rendering and LaTeX compilation
- Template Variables: Prepares data for Jinja template rendering
- LaTeX Compilation: Manages xelatex/pdflatex compilation process
- Error Tracking: Comprehensive error collection and reporting

Developer Notes:
- Requires properly preprocessed recipe content in _build/bodies/
- Uses Jinja2 for template rendering with strict whitespace control
- Runs LaTeX compiler twice to handle TOC/references correctly
- Maintains detailed error tracking for debugging
"""

from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime
import jinja2
import subprocess
from rich.console import Console
from rich.table import Table

from helpers import load_config, load_metadata
from indexer import CookbookIndexer

class BookCompiler:
    """Handles recipe book compilation process
    
    The compiler performs these key steps:
    1. Validates build state and preprocessed content
    2. Consolidates LaTeX package requirements
    3. Prepares template variables
    4. Renders LaTeX template
    5. Runs LaTeX compiler
    6. Generates compilation summary
    
    Error Handling:
    - All errors are collected in self.errors list
    - Each error includes phase, optional recipe, and error message
    - Compilation stops on critical errors
    """
    
    # LaTeX packages required for basic book functionality
    REQUIRED_PACKAGES = {
        'fontspec',    # Font handling
        'geometry',    # Page layout
        'titlesec',    # Section formatting
        'fancyhdr'     # Header/footer styling
    }
    
    # Files generated during LaTeX compilation that should be cleaned up
    AUXILIARY_EXTENSIONS = [
        '.aux',  # LaTeX auxiliary data
        '.log',  # Compilation log
        '.toc',  # Table of contents
        '.out'   # Hyperref output
    ]

    def __init__(self, config_path: Path, metadata_path: Path):
        """Initialize compiler with configuration and metadata
        
        Args:
            config_path: Path to book.yml configuration
            metadata_path: Path to build metadata
            
        The compiler requires both configuration and metadata to:
        - Load book settings and style preferences
        - Track build state and recipe processing status
        - Maintain consistent output locations
        """
        self.config = load_config(config_path)
        self.metadata = load_metadata(metadata_path)
        self.build_dir = Path(self.config['build']['output_dir'])
        self.template_dir = Path('_templates')
        
        # Add error tracking
        self.errors = []
        
        # Setup Jinja environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def validate_build_state(self) -> bool:
        """Validate build state and check if recipes need reprocessing
        
        Checks:
        - Existence of recipes in metadata
        - File modification times against last build
        - Presence of preprocessed content files
        
        Returns:
            bool: True if build state is valid and no rebuilds needed
        
        Side Effects:
            Adds validation errors to self.errors list
        """
        if not self.metadata['recipes']:
            self.errors.append({
                'phase': 'validation',
                'error': 'No recipes found in metadata'
            })
            return False

        needs_rebuild = False
        for recipe_path, recipe in self.metadata['recipes'].items():
            # Check if recipe changed since last build
            current_mtime = Path(recipe_path).stat().st_mtime
            if current_mtime > recipe.get('mtime', 0):
                needs_rebuild = True
                self.errors.append({
                    'phase': 'validation',
                    'recipe': recipe_path,
                    'error': 'Recipe modified since last build'
                })
                continue
            
            body_path = Path(recipe['extracted_body'])
            if not body_path.exists():
                self.errors.append({
                    'phase': 'validation',
                    'recipe': recipe_path,
                    'error': f'Preprocessed file missing: {body_path}'
                })
        
        return not needs_rebuild and len(self.errors) == 0

    def consolidate_packages(self) -> List[str]:
        """Consolidate LaTeX package requirements from all sources
        
        Combines packages from:
        - Individual recipe requirements
        - Template-required packages (REQUIRED_PACKAGES)
        - Optional packages based on configuration
        
        Returns:
            List[str]: Sorted list of unique LaTeX packages
        
        Side Effects:
            Updates self.metadata['packages'] with consolidated list
        """
        packages = set()
        
        # Get packages from recipes
        for recipe in self.metadata['recipes'].values():
            if recipe_packages := recipe.get('packages'):
                packages.update(recipe_packages)
        
        # Add template-required packages
        packages.update(self.REQUIRED_PACKAGES)
        
        # Add optional packages based on configuration
        if self.config['style'].get('include_toc'):
            packages.add('tocloft')
        if self.config['style'].get('include_index'):
            packages.add('makeidx')
        
        # Sort and update metadata
        sorted_packages = sorted(packages)
        self.metadata['packages'] = sorted_packages
        return sorted_packages

    def prepare_template_vars(self) -> Dict:
        """Prepare variables for template rendering
        
        Organizes data including:
        - Book title and authorship from config
        - Style settings from config
        - Consolidated package list
        - Recipes grouped and sorted by section
        
        Returns:
            Dict: Template variables ready for Jinja rendering
            
        Note:
            Section names are sorted alphabetically after stripping numeric prefixes
            Recipes within sections are sorted by title
        """
        template_vars = {
            # Copy config sections
            'title': self.config['title'],
            'authorship': self.config['authorship'],
            'style': self.config['style'],
            
            # Add consolidated packages
            'packages': self.metadata['packages'],
            
            # Organize recipes by section
            'sections': {}
        }
        
        # Get ordered section names, stripping numeric prefixes for sorting
        ordered_sections = sorted(
            set(recipe['section'] for recipe in self.metadata['recipes'].values()),
            key=lambda x: x.lstrip('0123456789-')
        )
        
        # Group and sort recipes by section
        for section in ordered_sections:
            # Get all recipes for this section
            section_recipes = [
                recipe for recipe in self.metadata['recipes'].values()
                if recipe['section'] == section
            ]
            # Sort recipes by title
            section_recipes.sort(key=lambda x: x.get('title', '').lower())
            template_vars['sections'][section] = section_recipes
        
        return template_vars

    def render_template(self) -> str:
        """Render the LaTeX template"""
        try:
            template = self.jinja_env.get_template(self.config['template'])
            template_vars = self.prepare_template_vars()
            return template.render(**template_vars)
        
        except jinja2.TemplateError as e:
            logging.error(f"Template rendering failed: {str(e)}")
            raise

    def run_latex_compiler(self, tex_path: Path, output_path: Path) -> bool:
        """Run LaTeX compiler to generate PDF output
        
        Executes LaTeX compiler twice to handle:
        1. Initial content and references
        2. Table of contents and cross-references
        
        After successful compilation, cleans up auxiliary files
        like .aux, .log, .toc, etc.
        
        Args:
            tex_path: Path to input .tex file
            output_path: Desired PDF output location
        
        Returns:
            bool: True if compilation succeeded, False if errors occurred
            
        Side Effects:
            - Creates PDF at output_path
            - Adds any compilation errors to self.errors
            - Removes auxiliary files after successful compilation
        """
        compiler = self.config.get('latex_compiler', 'xelatex')
        
        try:
            # Run compiler twice for TOC/references
            for run in range(2):
                logging.info(f"LaTeX compilation run {run + 1}/2")
                result = subprocess.run(
                    [compiler, '-interaction=nonstopmode', str(tex_path)],
                    cwd=self.build_dir,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    self.errors.append({
                        'phase': 'latex',
                        'error': result.stderr
                    })
                    return False
            
            # Clean up auxiliary files
            for ext in self.AUXILIARY_EXTENSIONS:
                aux_file = tex_path.with_suffix(ext)
                if aux_file.exists():
                    aux_file.unlink()
            
            return True
            
        except subprocess.SubprocessError as e:
            self.errors.append({
                'phase': 'latex',
                'error': str(e)
            })
            return False

    def print_compilation_summary(self, pdf_path: Optional[Path] = None):
        """Print a summary of the compilation process"""
        console = Console()
        
        # Print summary statistics
        total_recipes = len(self.metadata['recipes'])
        total_packages = len(self.metadata.get('packages', []))
        error_count = len(self.errors)
        
        console.print("\n[bold]Compilation Summary:[/bold]")
        console.print(f"• Total recipes: {total_recipes}")
        console.print(f"• Total packages: {total_packages}")
        console.print(f"• Errors: [red]{error_count}[/red]\n")
        
        if pdf_path:
            console.print(f"Output: [green]{pdf_path}[/green]\n")
        
        # Create recipes table
        recipe_table = Table(title="Recipe Processing Status")
        recipe_table.add_column("Section", style="cyan")
        recipe_table.add_column("Recipes", justify="right")
        recipe_table.add_column("Status", justify="center")
        
        # Group recipes by section
        sections = {}
        for recipe in self.metadata['recipes'].values():
            section = recipe['section']
            if section not in sections:
                sections[section] = {'total': 0, 'errors': 0}
            sections[section]['total'] += 1
            if any(e.get('recipe') == recipe['path'] for e in self.errors):
                sections[section]['errors'] += 1
        
        # Add rows for each section
        for section, counts in sorted(sections.items()):
            status = "[green]OK[/green]" if counts['errors'] == 0 else f"[red]{counts['errors']} errors[/red]"
            recipe_table.add_row(section, str(counts['total']), status)
        
        console.print(recipe_table)
        
        # Print errors table if any exist
        if self.errors:
            error_table = Table(title="\nErrors Encountered")
            error_table.add_column("Phase", style="magenta")
            error_table.add_column("Recipe", style="cyan")
            error_table.add_column("Error", style="red", no_wrap=False)
            
            for error in self.errors:
                error_table.add_row(
                    error['phase'],
                    error.get('recipe', '-'),
                    error['error']
                )
            
            console.print(error_table)

    def compile(self) -> Optional[Path]:
        """Execute full compilation pipeline
        
        Pipeline steps:
        1. Validate build state and dependencies
        2. Consolidate required LaTeX packages
        3. Render template with recipe content
        4. Generate index if configured
        5. Run LaTeX compiler
        
        Returns:
            Path: Path to compiled PDF on success
            None: If any step fails
            
        Raises:
            ValueError: If build validation fails
            
        Side Effects:
            - Creates intermediate .tex files
            - Generates final PDF
            - Tracks errors in self.errors
        """
        self.errors = []  # Reset errors
        
        if not self.validate_build_state():
            raise ValueError("Build state validation failed")

        try:
            # Consolidate packages
            packages = self.consolidate_packages()
            
            # Render template
            try:
                rendered_content = self.render_template()
            except jinja2.TemplateError as e:
                self.errors.append({
                    'phase': 'template',
                    'error': str(e)
                })
                return None
            
            # Save rendered content
            tex_path = self.build_dir / 'book.tex'
            tex_path.write_text(rendered_content, encoding='utf-8')
            
            # Add indexing step
            if self.config['style'].get('include_index'):
                try:
                    indexer = CookbookIndexer()
                    indexed_tex_path = self.build_dir / 'book_indexed.tex'
                    indexer.process_cookbook(tex_path, indexed_tex_path)
                    tex_path = indexed_tex_path  # Use indexed version for compilation
                except Exception as e:
                    self.errors.append({
                        'phase': 'indexing',
                        'error': str(e)
                    })
                    return None
            
            # Run LaTeX compiler
            pdf_path = self.build_dir / 'book.pdf'
            if not self.run_latex_compiler(tex_path, pdf_path):
                return None
            
            return pdf_path

        except Exception as e:
            self.errors.append({
                'phase': 'compilation',
                'error': str(e)
            })
            raise

def main():
    """Command-line entry point for recipe book compilation
    
    Workflow:
    1. Configure logging
    2. Initialize compiler with config/metadata
    3. Run compilation pipeline
    4. Generate summary report
    5. Set exit code based on success/failure
    
    Exit Codes:
        0: Successful compilation with PDF output
        1: Compilation failed (see error details in summary)
    
    Side Effects:
        - Creates build artifacts in output directory
        - Prints compilation summary to console
        - Logs detailed progress information
    """
    logging.basicConfig(level=logging.INFO)
    
    config_path = Path('_tools/book.yml')
    metadata_path = Path('_build/metadata.yml')
    
    compiler = BookCompiler(config_path, metadata_path)
    
    try:
        pdf_path = compiler.compile()
        if pdf_path:
            compiler.print_compilation_summary(pdf_path)
            logging.info(f"Successfully compiled recipe book: {pdf_path}")
        else:
            compiler.print_compilation_summary()
            logging.error("Compilation failed")
            exit(1)
    except Exception as e:
        compiler.print_compilation_summary()
        logging.error(f"Compilation error: {str(e)}")
        exit(1)

if __name__ == '__main__':
    main() 