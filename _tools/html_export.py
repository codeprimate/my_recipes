"""Recipe book HTML export module

This module handles the conversion of recipe books to HTML format by generating
HTML directly from template variables, similar to the LaTeX compilation process.

Key Components:
- HTMLExporter: Main class handling HTML generation and template rendering
- LaTeX to HTML Converter: Converts LaTeX recipe bodies to HTML
- Template Rendering: Generates complete HTML with embedded CSS
- Error Tracking: Comprehensive error collection and reporting

Developer Notes:
- No external dependencies (no Pandoc required)
- Uses Jinja2 for HTML template rendering
- Outputs single self-contained HTML file with embedded CSS
- Templates located in _tools/templates/web/
- Reads preprocessed recipe content from _build/bodies/
"""

from pathlib import Path
from typing import Optional, Dict
import logging
import re
import jinja2
from datetime import datetime
from rich.console import Console

from helpers import load_config, load_metadata


class LaTeXToHTMLConverter:
    """Converts LaTeX recipe content to HTML"""
    
    def convert(self, latex_content: str) -> str:
        """Convert LaTeX content to HTML
        
        Args:
            latex_content: LaTeX source content
            
        Returns:
            str: HTML content
        """
        html = latex_content
        
        # Convert sections
        html = re.sub(r'\\section\*\{([^}]+)\}', r'<h3>\1</h3>', html)
        html = re.sub(r'\\section\{([^}]+)\}', r'<h3>\1</h3>', html)
        
        # Convert text formatting
        html = re.sub(r'\\textbf\{([^}]+)\}', r'<strong>\1</strong>', html)
        html = re.sub(r'\\textit\{([^}]+)\}', r'<em>\1</em>', html)
        html = re.sub(r'\\emph\{([^}]+)\}', r'<em>\1</em>', html)
        
        # Convert multicols environment to HTML structure
        html = self._convert_multicols(html)
        
        # Convert enumerate - handle multiline items
        html = re.sub(r'\\begin\{enumerate\}(.*?)\\end\{enumerate\}', 
                      lambda m: self._convert_enumerate(m.group(1)), 
                      html, flags=re.DOTALL)
        
        # Convert itemize
        html = re.sub(r'\\begin\{itemize\}', '<ul>', html)
        html = re.sub(r'\\end\{itemize\}', '</ul>', html)
        
        # Convert dotfill to CSS-based dotted line
        html = re.sub(r'\\dotfill', '<span class="dotfill"></span>', html)
        
        # Convert line breaks
        html = re.sub(r'\\\\', '<br>', html)
        html = re.sub(r'\\newline', '<br>', html)
        
        # Convert noindent
        html = re.sub(r'\\noindent\s*', '', html)
        
        # Convert non-breaking spaces
        html = re.sub(r'~', '&nbsp;', html)
        
        # Convert quotes
        html = re.sub(r'``', '"', html)
        html = re.sub(r"''", '"', html)
        html = re.sub(r'`', "'", html)
        
        # Remove LaTeX-specific commands that don't translate
        html = re.sub(r'\\setlength\{[^}]+\}', '', html)
        html = re.sub(r'\\columnbreak', '', html)
        html = re.sub(r'\\vspace\*?\{[^}]+\}', '', html)
        html = re.sub(r'\\hspace\*?\{[^}]+\}', '', html)
        html = re.sub(r'\\hrulefill', '<hr class="section-divider">', html)
        
        # Clean up extra whitespace
        html = re.sub(r'\n\s*\n\s*\n+', '\n\n', html)
        html = html.strip()
        
        return html
    
    def _convert_enumerate(self, content: str) -> str:
        """Convert enumerate environment content to HTML ordered list
        
        Args:
            content: Content between \begin{enumerate} and \end{enumerate}
            
        Returns:
            str: HTML ordered list
        """
        items = re.split(r'\\item\s+', content)
        if len(items) <= 1:
            return '<ol></ol>'
        
        html = '<ol>\n'
        for item in items[1:]:  # Skip first empty part before first \item
            item = item.strip()
            if item:
                # Remove trailing \\ if present
                item = re.sub(r'\\\\\s*$', '', item)
                html += f'    <li>{item}</li>\n'
        html += '</ol>'
        return html
    
    def _convert_multicols(self, html: str) -> str:
        """Convert multicols environment to HTML grid
        
        Args:
            html: HTML content with multicols
            
        Returns:
            str: HTML with multicols converted to grid
        """
        # Find multicols blocks
        pattern = r'\\begin\{multicols\}\{(\d+)\}(.*?)\\end\{multicols\}'
        
        def replace_multicols(match):
            cols = int(match.group(1))
            content = match.group(2)
            
            # Split content by \columnbreak
            parts = content.split('\\columnbreak')
            
            # Wrap in grid container
            grid_html = '<div class="ingredients-columns">\n'
            
            # Process all lines, handling both columns
            all_lines = []
            for part in parts:
                lines = part.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('%'):
                        all_lines.append(line)
            
            for line in all_lines:
                # Convert ingredient line format: "Item \dotfill Amount \\"
                # Replace \dotfill with HTML span, remove trailing \\
                line = line.replace('\\\\', '').strip()
                # Convert \dotfill to HTML
                if '\\dotfill' in line:
                    # Split on dotfill to get name and amount
                    parts = line.split('\\dotfill')
                    if len(parts) == 2:
                        name = parts[0].strip()
                        amount = parts[1].strip()
                        grid_html += f'    <div class="ingredient-item"><span class="ingredient-name">{name}</span><span class="dotfill"></span><span class="ingredient-amount">{amount}</span></div>\n'
                    else:
                        grid_html += f'    <div class="ingredient-item">{line}</div>\n'
                else:
                    grid_html += f'    <div class="ingredient-item">{line}</div>\n'
            
            grid_html += '</div>'
            return grid_html
        
        return re.sub(pattern, replace_multicols, html, flags=re.DOTALL)


class HTMLExporter:
    """Handles recipe book HTML export process
    
    The exporter performs these key steps:
    1. Validates build state and preprocessed content
    2. Converts LaTeX recipe bodies to HTML
    3. Prepares template variables (same as LaTeX compiler)
    4. Renders HTML template with embedded CSS
    5. Saves final HTML file
    
    Error Handling:
    - All errors are collected in self.errors list
    - Each error includes phase and error message
    - Export stops on critical errors
    """
    
    def __init__(self, config_path: Path):
        """Initialize exporter with configuration
        
        Args:
            config_path: Path to book.yml configuration
            
        The exporter requires configuration to:
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
        self.template_dir = config_path.parent / "templates" / "web"
        self.errors = []
        self.converter = LaTeXToHTMLConverter()
        
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        self.console = Console()
    
    def validate_build_state(self) -> bool:
        """Validate build state and check if recipes are preprocessed
        
        Returns:
            bool: True if build state is valid
            
        Side Effects:
            Adds validation errors to self.errors list
        """
        if not self.metadata.get('recipes'):
            self.errors.append({
                'phase': 'validation',
                'error': 'No recipes found in metadata'
            })
            return False
        
        # Check if recipes are preprocessed
        for recipe_path, recipe in self.metadata['recipes'].items():
            if not recipe.get('preprocessed', False):
                self.errors.append({
                    'phase': 'validation',
                    'recipe': recipe_path,
                    'error': 'Recipe not preprocessed'
                })
                return False
            
            # Check if preprocessed file exists
            if 'extracted_body' in recipe:
                body_path = self.build_dir / recipe['extracted_body']
                if not body_path.exists():
                    self.errors.append({
                        'phase': 'validation',
                        'recipe': recipe_path,
                        'error': f'Preprocessed file missing: {recipe["extracted_body"]}'
                    })
                    return False
        
        return True
    
    def convert_recipe_to_html(self, recipe_path: Path) -> str:
        """Convert a single recipe LaTeX file to HTML
        
        Args:
            recipe_path: Path to preprocessed LaTeX recipe file
            
        Returns:
            str: HTML content for the recipe
        """
        try:
            content = recipe_path.read_text(encoding='utf-8')
            return self.converter.convert(content)
        except Exception as e:
            self.errors.append({
                'phase': 'conversion',
                'recipe': str(recipe_path),
                'error': f'Failed to convert recipe: {str(e)}'
            })
            return f'<p class="error">Error converting recipe: {str(e)}</p>'
    
    def prepare_template_vars(self) -> Dict:
        """Prepare variables for HTML template rendering
        
        Uses the same approach as BookCompiler.prepare_template_vars()
        but converts recipe bodies to HTML instead of LaTeX.
        
        Returns:
            Dict: Template variables including:
                - title: Book title
                - authorship: Author info
                - style: Style settings
                - sections: Dict of recipes grouped by section (with HTML content)
        """
        # Convert last_build timestamp to datetime
        last_build = datetime.fromisoformat(self.metadata.get('last_build', datetime.now().isoformat()))
        
        template_vars = {
            'title': self.config['title'],
            'authorship': {
                **self.config['authorship'],
                'date': last_build.strftime('%Y Edition - %B')
            },
            'style': self.config['style'],
            'sections': {},
            'include_toc': self.config['style'].get('include_toc', True)
        }
        
        # Get ordered section names
        ordered_sections = sorted(
            set(recipe['section'] for recipe in self.metadata['recipes'].values()),
            key=lambda x: x.lstrip('0123456789-')
        )
        
        # Group and sort recipes by section, converting to HTML
        for section in ordered_sections:
            section_recipes = []
            for recipe in self.metadata['recipes'].values():
                if recipe['section'] == section:
                    # Convert recipe body to HTML
                    body_path = self.build_dir / recipe['extracted_body']
                    html_content = self.convert_recipe_to_html(body_path)
                    
                    section_recipes.append({
                        'title': recipe['title'],
                        'html_content': html_content
                    })
            
            section_recipes.sort(key=lambda x: x['title'].lower())
            template_vars['sections'][section] = section_recipes
        
        return template_vars
    
    def render_html_template(self, template_vars: Dict) -> str:
        """Render HTML template with embedded CSS
        
        Args:
            template_vars: Template variables prepared by prepare_template_vars()
            
        Returns:
            str: Complete HTML document with embedded CSS
            
        Raises:
            jinja2.TemplateError: If template rendering fails
            
        Side Effects:
            Adds template errors to self.errors list
        """
        try:
            template = self.jinja_env.get_template('book.html.jinja')
            return template.render(**template_vars)
            
        except jinja2.TemplateNotFound:
            self.errors.append({
                'phase': 'template',
                'error': f'HTML template not found: {self.template_dir}/book.html.jinja'
            })
            raise
        except jinja2.TemplateError as e:
            self.errors.append({
                'phase': 'template',
                'error': f'Template rendering failed: {str(e)}'
            })
            raise
    
    def export_html(self) -> Optional[Path]:
        """Export recipe book to HTML format
        
        Returns:
            Optional[Path]: Path to exported HTML file if successful, None otherwise
            
        The export process:
        1. Validates build state
        2. Converts LaTeX recipe bodies to HTML
        3. Prepares template variables
        4. Renders HTML template
        5. Saves final HTML file
        """
        self.console.print("\n[bold cyan]╔══ HTML Export ══╗[/bold cyan]")
        
        # Validate build state
        with self.console.status("[yellow]Validating build state...", spinner="dots"):
            if not self.validate_build_state():
                self.console.print("[red]✗ Build state validation failed[/red]")
                return None
            self.console.print("[green]✓ Build state validated[/green]")
        
        # Prepare template variables (converts recipes to HTML)
        with self.console.status("[yellow]Converting recipes to HTML...", spinner="dots"):
            template_vars = self.prepare_template_vars()
            recipe_count = sum(len(recipes) for recipes in template_vars['sections'].values())
            self.console.print(f"[green]✓ Converted {recipe_count} recipes to HTML[/green]")
        
        # Render template
        with self.console.status("[yellow]Rendering HTML template...", spinner="dots"):
            try:
                final_html = self.render_html_template(template_vars)
                self.console.print("[green]✓ Template rendered[/green]")
            except jinja2.TemplateError:
                return None
        
        # Save HTML file
        html_output_dir = self.build_dir / self.config['build'].get('html_output_dir', 'html')
        html_output_dir.mkdir(exist_ok=True)
        html_path = html_output_dir / "book.html"
        
        with self.console.status("[yellow]Saving HTML file...", spinner="dots"):
            html_path.write_text(final_html, encoding='utf-8')
            self.console.print(f"[green]✓ HTML saved to {html_path}[/green]")
        
        self.console.print(f"\n[green bold]✓ Successfully exported: {html_path}[/green bold]")
        return html_path
    
    def print_export_summary(self, html_path: Optional[Path] = None):
        """Print a summary of the HTML export process
        
        Args:
            html_path: Optional path to the exported HTML file
        """
        console = Console()
        
        error_count = len(self.errors)
        
        console.print("\n[bold]HTML Export Summary:[/bold]")
        console.print(f"• Errors: [red]{error_count}[/red]\n")
        
        if html_path:
            console.print(f"Output: [green]{html_path}[/green]\n")
        
        # Print errors table if any exist
        if self.errors:
            from rich.table import Table
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


def main():
    """Command-line entry point for HTML export"""
    import sys
    logging.basicConfig(level=logging.INFO)
    
    # Use absolute paths resolved from project root
    project_root = Path(__file__).parent.parent
    config_path = project_root / '_tools/book.yml'
    
    exporter = HTMLExporter(config_path)
    
    try:
        html_path = exporter.export_html()
        if html_path:
            exporter.print_export_summary(html_path)
            logging.info(f"Successfully exported recipe book: {html_path}")
        else:
            exporter.print_export_summary()
            logging.error("HTML export failed")
            exit(1)
    except Exception as e:
        exporter.print_export_summary()
        logging.error(f"Export error: {str(e)}")
        exit(1)


if __name__ == '__main__':
    main()
