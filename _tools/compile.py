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
from datetime import datetime, timedelta
import jinja2
import subprocess
import re
from rich.console import Console
from rich.table import Table

from helpers import load_config, load_metadata
# from cookbook_indexer import CookbookIndexer

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
        'fancyhdr',    # Header/footer styling
        'afterpage'    # For empty page handling (only used if twoside)
    }
    
    # Files generated during LaTeX compilation that should be cleaned up
    AUXILIARY_EXTENSIONS = [
        '.aux',  # LaTeX auxiliary data
        '.log',  # Compilation log
        '.toc',  # Table of contents
        '.out'   # Hyperref output
        '.sty'
    ]

    def __init__(self, config_path: Path):
        """Initialize compiler with configuration
        
        Args:
            config_path: Path to book.yml configuration
            
        The compiler requires configuration to:
        - Load book settings and style preferences
        - Track build state and recipe processing status
        - Maintain consistent output locations
        
        Side Effects:
            - Initializes self.config from config_path
            - Sets up build and template directories
            - Creates Jinja environment with specific settings
            - Initializes empty errors list
        """
        self.config = load_config(config_path)
        self.build_dir = Path(self.config['build']['output_dir']).resolve()
        self.metadata = load_metadata(self.build_dir / "metadata.yml")
        self.template_dir = config_path.parent
        self.errors = []

        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

        self.console = Console()

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
            try:
                # Convert ISO datetime string to timestamp if needed
                stored_mtime = recipe.get('mtime', 0)
                if isinstance(stored_mtime, str):
                    stored_mtime = datetime.fromisoformat(stored_mtime).timestamp()
                else:
                    stored_mtime = float(stored_mtime)
                
                current_mtime = Path(recipe_path).stat().st_mtime
                
                # Only flag as needing rebuild if:
                # 1. File was modified after last processing AND
                # 2. Either no extracted body exists or preprocessing isn't complete
                if current_mtime > stored_mtime and (
                    not recipe.get('extracted_body') or 
                    not recipe.get('preprocessed', False)
                ):
                    needs_rebuild = True
                    self.errors.append({
                        'phase': 'validation',
                        'recipe': recipe_path,
                        'error': 'Recipe needs processing'
                    })
                    continue
                
                # Check if preprocessed file exists using build_dir
                if 'extracted_body' in recipe:
                    body_path = self.build_dir / recipe['extracted_body']
                    if not body_path.exists():
                        self.errors.append({
                            'phase': 'validation',
                            'recipe': recipe_path,
                            'error': f'Preprocessed file missing: {recipe["extracted_body"]}'
                        })
            except (ValueError, TypeError) as e:
                self.errors.append({
                    'phase': 'validation',
                    'recipe': recipe_path,
                    'error': f'Invalid mtime value: {str(e)}'
                })
                
        return True

    def consolidate_packages(self) -> List[str]:
        """Consolidate LaTeX package requirements from all sources
        
        Combines packages from:
        - Individual recipe requirements
        - Template-required packages (REQUIRED_PACKAGES)
        - Optional packages based on configuration
        
        Returns:
            List[str]: Sorted list of unique LaTeX packages
        
        Side Effects:
            - Updates self.metadata['packages'] with consolidated list
            - Adds tocloft if TOC is enabled in config
            - Adds makeidx if index is enabled in config
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
        - Last build timestamp formatted for display
        
        Returns:
            Dict: Template variables including:
                - title: Book title from config
                - authorship: Author info and formatted date
                - style: Style settings from config
                - packages: Consolidated LaTeX packages
                - sections: Dict of recipes grouped by section
                - index: Include index
                
        Note:
            - Section names are sorted alphabetically after stripping numeric prefixes
            - Recipes within sections are sorted by title
            - Recipe paths have spaces escaped for LaTeX compatibility
        """
        # Convert last_build timestamp to datetime
        last_build = datetime.fromisoformat(self.metadata.get('last_build', datetime.now().isoformat()))
        
        template_vars = {
            # Copy config sections
            'title': self.config['title'],
            'authorship': {
                **self.config['authorship'],
                'date': last_build.strftime('%Y Edition - %B')
            },
            'style': self.config['style'],
            
            # Add consolidated packages
            'packages': self.metadata['packages'],
            
            # Organize recipes by section
            'sections': {},
            
            # Add twoside flag directly to template vars
            'twoside': self.config['style'].get('twoside', False),

            # Add index flag directly to template vars
            'index': self.config['style'].get('include_index', False)
        }
        
        # Helper function to extract numeric prefix for sorting
        def get_section_sort_key(section_name: str) -> tuple:
            """Extract numeric prefix for sorting, return (number, name) tuple"""
            match = re.match(r'^(\d+)\s*[-]?\s*(.+)', section_name)
            if match:
                return (int(match.group(1)), section_name)
            # No numeric prefix - sort alphabetically after numbered sections
            return (999, section_name)
        
        # Get ordered section names (sorted by numeric prefix if present)
        ordered_sections = sorted(
            set(recipe['section'] for recipe in self.metadata['recipes'].values()),
            key=get_section_sort_key
        )
        
        # Group and sort recipes by section, using formatted title from metadata for display
        for section in ordered_sections:
            # Get formatted section title from metadata (already has numbers stripped by scan.py)
            formatted_title = self.metadata.get('sections', {}).get(section, section)
            
            section_recipes = [
                {
                    **recipe,
                    # Only escape spaces if extracted_body is a string
                    'extracted_body': recipe['extracted_body'].replace(' ', '\ ') if isinstance(recipe['extracted_body'], str) else recipe['extracted_body']
                }
                for recipe in self.metadata['recipes'].values()
                if recipe['section'] == section
            ]
            section_recipes.sort(key=lambda x: x.get('title', '').lower())
            # Use formatted title from metadata as the key for template
            template_vars['sections'][formatted_title] = section_recipes
        
        # Add recently modified recipes (flat list, configurable limit)
        revisions_limit = self.config['style'].get('revisions_limit', 30)
        template_vars['recently_modified'] = self._get_recently_modified_recipes(revisions_limit)
        
        return template_vars

    def _get_recently_modified_recipes(self, limit: int = 30) -> List[Dict]:
        """Get the latest modified recipes ordered by calendar day then recipe name.
        
        Args:
            limit: Maximum number of recipes to return (default: 30)
        
        Returns:
            List of recipe dicts, each containing:
                - title: Recipe title
                - date: Formatted date string (e.g., "January 5, 2026")
                - mtime: Original modification time for sorting
            Sorted by calendar day (descending, newest first), then by recipe name (ascending),
            limited to `limit` items.
        """
        all_recipes = []
        
        for recipe_path, recipe in self.metadata['recipes'].items():
            try:
                # Parse modification time
                mtime_str = recipe.get('mtime', '')
                if not mtime_str:
                    continue
                
                if isinstance(mtime_str, str):
                    mtime = datetime.fromisoformat(mtime_str)
                else:
                    # Fallback for numeric timestamps
                    mtime = datetime.fromtimestamp(float(mtime_str))
                
                # Format date for display (e.g., "January 5, 2026")
                # Use %d and strip leading zero for cross-platform compatibility
                day = mtime.day
                date_str = mtime.strftime(f'%B {day}, %Y')
                
                recipe_data = {
                    'title': recipe.get('title', ''),
                    'date': date_str,
                    'mtime': mtime
                }
                
                all_recipes.append(recipe_data)
                    
            except (ValueError, TypeError) as e:
                # Skip recipes with invalid mtime
                logging.debug(f"Skipping recipe {recipe_path} due to invalid mtime: {e}")
                continue
        
        # Sort by calendar day (descending, newest first), then by recipe name (ascending)
        all_recipes.sort(key=lambda x: (
            -x['mtime'].toordinal(),  # Negative for descending order (newest day first)
            x['title'].lower()  # Recipe name ascending
        ))
        return all_recipes[:limit]

    def render_template(self, packages: List[str]) -> str:
        """Render the LaTeX template
        
        Returns:
            str: Rendered LaTeX content as string
            
        Raises:
            jinja2.TemplateError: If template rendering fails
                Including TemplateSyntaxError with line number details
            
        Side Effects:
            - Logs debug information about template variables
            - Adds template errors to self.errors list
            - Logs detailed error information on failure
        """
        try:
            template = self.jinja_env.get_template(self.config['template'])
            template_vars = self.prepare_template_vars()
            
            # Add debug logging for template variables
            logging.debug("Template variables:")
            for key, value in template_vars.items():
                logging.debug(f"  {key}: {type(value)}")
            
            return template.render(**template_vars)
        
        except jinja2.TemplateError as e:
            # Add more detailed error information
            logging.error(f"Template rendering failed: {str(e)}")
            if isinstance(e, jinja2.TemplateSyntaxError):
                logging.error(f"Error occurred on line {e.lineno}")
                logging.error(f"In template: {e.filename}")
                logging.error(f"Near: {e.message}")
            self.errors.append({
                'phase': 'template',
                'error': f"{str(e)} (line {getattr(e, 'lineno', 'unknown')})"
            })
            raise

    def run_latex_compiler(self, tex_path: Path, output_path: Path) -> bool:
        """Run LaTeX compiler to generate PDF output"""
        compiler = self.config['build'].get('latex_compiler', 'xelatex')
        
        try:
            # Track which file we're actually compiling
            current_tex_path = tex_path
            
            # Run compiler twice for TOC/references
            for run in range(2):
                self.console.print(f"[cyan]LaTeX Pass {run + 1}/2[/cyan]")
                
                # After first pass, process for indexing if needed
                # if run == 0 and self.config['style'].get('include_index'):
                #     with self.console.status("[yellow]Processing index terms...", spinner="dots"):
                #         result = subprocess.run(
                #             ['latexpand', str(tex_path)],
                #             cwd=self.build_dir,
                #             capture_output=True,
                #             text=True
                #         )
                #         if result.returncode == 0:
                #             expanded_path = tex_path.with_suffix('.expanded.tex')
                #             expanded_path.write_text(result.stdout)
                #             self.console.print("[green]✓ Created expanded version[/green]")
                            
                #             # Process the expanded version for indexing
                #             indexer = CookbookIndexer(expanded_path)
                #             indexer.process()
                            
                #             # Rename the expanded index file to match the base name
                #             expanded_idx = tex_path.with_suffix('.expanded.idx')
                #             if expanded_idx.exists():
                #                 idx_path = tex_path.with_suffix('.idx')
                #                 expanded_idx.rename(idx_path)
                            
                #             # Use the expanded version for the second pass
                #             current_tex_path = expanded_path
                #             self.console.print("[green]✓ Index terms processed[/green]")
                #         else:
                #             self.console.print("[red]✗ Failed to process index terms[/red]")
                #             self.errors.append({
                #                 'phase': 'expansion',
                #                 'error': result.stderr
                #             })
                #             return False
                
                # Compile with the current input file
                with self.console.status("[bold yellow]Compiling...", spinner="dots"):
                    result = subprocess.run(
                        [
                            compiler,
                            '-interaction=nonstopmode',
                            f'-jobname={tex_path.stem}',  # Ensure consistent output filename
                            str(current_tex_path)
                        ],
                        cwd=self.build_dir,
                        capture_output=True,
                        text=True
                    )
                
                # Check for actual error indicators in the output
                if "Fatal error occurred" in result.stdout or "Emergency stop" in result.stdout:
                    self.console.print("[red]✗ Compilation failed[/red]")
                    error_message = result.stderr if result.stderr else "LaTeX compilation failed"
                    self.errors.append({
                        'phase': 'latex',
                        'error': error_message
                    })

                    self.console.print("\n[bold red]LaTeX Compiler Output:[/bold red]")
                    self.console.print(result.stdout)
                    return False
                
                self.console.print("[green]✓ Pass completed successfully[/green]")

            # Clean up auxiliary files and expanded version
            with self.console.status("[dim]Removing temporary files", spinner="dots"):
                for ext in self.AUXILIARY_EXTENSIONS:
                    aux_file = tex_path.with_suffix(ext)
                    if aux_file.exists():
                        aux_file.unlink()
                
                # Clean up expanded version if it exists
                expanded_path = tex_path.with_suffix('.expanded.tex')
                if expanded_path.exists():
                    expanded_path.unlink()
            
            self.console.print("[green]✓ Cleanup complete[/green]")
            return True
            
        except subprocess.SubprocessError as e:
            self.errors.append({
                'phase': 'latex',
                'error': str(e)
            })
            return False

    def print_compilation_summary(self, pdf_path: Optional[Path] = None):
        """Print a summary of the compilation process
        
        Args:
            pdf_path: Optional path to the compiled PDF file
            
        Displays:
            - Total number of recipes processed
            - Total number of LaTeX packages used
            - Error count
            - Recipe processing status by section
            - Detailed error table if errors occurred
            - Output PDF path if successful
            
        Side Effects:
            - Prints formatted tables using rich library
            - Shows color-coded status indicators
            - Groups and summarizes errors by phase
        """
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
        for recipe_path, recipe in self.metadata['recipes'].items():
            section = recipe['section']
            if section not in sections:
                sections[section] = {'total': 0, 'errors': 0}
            sections[section]['total'] += 1
            if any(e.get('recipe') == recipe_path for e in self.errors):
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
        """Compile the recipe book into final PDF"""
        
        self.console.print("\n[bold cyan]╔══ Book Compilation ══╗[/bold cyan]")
        
        # Validate build state
        with self.console.status("[yellow]Validating build state...", spinner="dots") as status:
            if not self.validate_build_state():
                self.console.print("[red]✗ Build state validation failed[/red]")
                return None
            self.console.print("[green]✓ Build state validated[/green]")
            
            # Consolidate packages
            status.update("[yellow]Consolidating LaTeX packages...")
            packages = self.consolidate_packages()
            self.console.print(f"[green]✓ Found {len(packages)} required packages[/green]")
            
            # Render template
            status.update("[yellow]Rendering LaTeX template...")
            content = self.render_template(packages)
            self.console.print("[green]✓ Template rendered[/green]")
            
            # Save content
            status.update("[yellow]Saving rendered content...")
            tex_path = self.build_dir / "book.tex"
            tex_path.write_text(content)
            self.console.print(f"[green]✓ Content saved to {tex_path.name}[/green]")

            # Generate index if enabled
            # if self.config['style'].get('include_index'):
            #     status.update("[yellow]Generating index...")
            #     indexer = CookbookIndexer(tex_path)
            #     try:
            #         indexer.process()
            #         self.console.print("[green]✓ Index generated[/green]")
            #     except Exception as e:
            #         self.console.print("[red]✗ Index generation failed[/red]")
            #         self.errors.append({
            #             'phase': 'index',
            #             'error': str(e)
            #         })
            #         return None
        
        # Run LaTeX compiler
        self.console.print("\n[bold cyan]╔══ LaTeX Compilation ══╗[/bold cyan]")
        output_path = self.build_dir / "book.pdf"
        if not self.run_latex_compiler(tex_path, output_path):
            return None
        
        if output_path.exists():
            self.console.print(f"\n[green bold]✓ Successfully compiled: {output_path}[/green bold]")
            return output_path
        
        return None

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
        - Sets process exit code
        - Configures logging to INFO level
    """
    logging.basicConfig(level=logging.INFO)
    
    # Use absolute paths resolved from project root
    project_root = Path(__file__).parent.parent
    config_path = project_root / '_tools/book.yml'
    
    compiler = BookCompiler(config_path)
    
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