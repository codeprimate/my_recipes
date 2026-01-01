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
    
    def _convert_text_formatting(self, text: str) -> str:
        """Recursively convert text formatting commands
        
        Args:
            text: Text that may contain formatting commands
            
        Returns:
            str: Text with formatting converted to HTML
        """
        # Convert text formatting (handle nested braces by processing from inside out)
        # We need to handle nested braces, so we'll do multiple passes
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            original = text
            
            # Convert textbf (bold)
            text = re.sub(r'\\textbf\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', r'<strong>\1</strong>', text)
            
            # Convert textit (italic)
            text = re.sub(r'\\textit\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', r'<em>\1</em>', text)
            
            # Convert emph (emphasis/italic)
            text = re.sub(r'\\emph\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', r'<em>\1</em>', text)
            
            # If no changes were made, we're done
            if text == original:
                break
        
        return text
    
    def convert(self, latex_content: str) -> str:
        """Convert LaTeX content to HTML
        
        Args:
            latex_content: LaTeX source content
            
        Returns:
            str: HTML content
        """
        html = latex_content
        
        # Remove LaTeX-specific layout commands first
        html = re.sub(r'\\setlength\{[^}]+\}', '', html)
        html = re.sub(r'\\columnbreak', '', html)
        html = re.sub(r'\\vspace\*?\{[^}]+\}', '', html)
        html = re.sub(r'\\hspace\*?\{[^}]+\}', '', html)
        html = re.sub(r'\\noindent\s*', '', html)
        html = re.sub(r'\\newpage', '<div class="page-break"></div>', html)
        
        # Convert sections and subsections
        html = re.sub(r'\\section\*\{([^}]+)\}', r'<h3>\1</h3>', html)
        html = re.sub(r'\\section\{([^}]+)\}', r'<h3>\1</h3>', html)
        html = re.sub(r'\\subsection\*\{([^}]+)\}', r'<h4>\1</h4>', html)
        html = re.sub(r'\\subsection\{([^}]+)\}', r'<h4>\1</h4>', html)
        
        # Convert enumerate environments first (before multicols, so nested lists work)
        html = re.sub(r'\\begin\{enumerate\}(.*?)\\end\{enumerate\}', 
                      lambda m: self._convert_enumerate(m.group(1)), 
                      html, flags=re.DOTALL)
        
        # Convert itemize environments (before multicols, so nested lists work)
        html = re.sub(r'\\begin\{itemize\}(.*?)\\end\{itemize\}', 
                      lambda m: self._convert_itemize(m.group(1)), 
                      html, flags=re.DOTALL)
        
        # Convert em environments (before quote, so nested environments work)
        html = re.sub(r'\\begin\{em\}(.*?)\\end\{em\}', 
                      r'<em>\1</em>', 
                      html, flags=re.DOTALL)
        
        # Convert quote environments (after em, so nested environments work)
        html = re.sub(r'\\begin\{quote\}(.*?)\\end\{quote\}', 
                      r'<blockquote>\1</blockquote>', 
                      html, flags=re.DOTALL)
        
        # Convert multicols environment to HTML structure (after lists are converted)
        html = self._convert_multicols(html)
        
        # Convert non-multicol ingredient lists (after multicols, before dotfill conversion)
        html = self._convert_nonmulticol_ingredients(html)
        
        # Convert text formatting (after environments are converted)
        # Use the helper method which handles nested braces
        html = self._convert_text_formatting(html)
        
        # Convert LaTeX fraction commands to HTML entities (handle both with and without braces)
        html = re.sub(r'\\textonehalf(\{\})?', '½', html)
        html = re.sub(r'\\textonequarter(\{\})?', '¼', html)
        html = re.sub(r'\\textthreequarter(\{\})?', '¾', html)
        html = re.sub(r'\\textonethird(\{\})?', '⅓', html)
        html = re.sub(r'\\texttwothirds(\{\})?', '⅔', html)
        
        # Convert dotfill to CSS-based dotted line
        html = re.sub(r'\\dotfill', '<span class="dotfill"></span>', html)
        
        # Convert line breaks
        html = re.sub(r'\\\\', '<br>', html)
        html = re.sub(r'\\newline', '<br>', html)
        
        # Convert non-breaking spaces
        html = re.sub(r'~', '&nbsp;', html)
        
        # Convert escaped ampersand (LaTeX \& to HTML &)
        html = re.sub(r'\\&', '&', html)
        
        # Convert escaped hash (LaTeX \# to HTML #)
        html = re.sub(r'\\#', '#', html)
        
        # Convert quotes
        html = re.sub(r'``', '"', html)
        html = re.sub(r"''", '"', html)
        html = re.sub(r'`', "'", html)
        
        # Convert em dash
        html = re.sub(r'---', '&mdash;', html)
        
        # Convert hrulefill
        html = re.sub(r'\\hrulefill', '<hr class="section-divider">', html)
        
        # Remove font size commands and braces
        html = re.sub(r'\\small\s*', '', html)
        html = re.sub(r'\\large\s*', '', html)
        html = re.sub(r'\\Large\s*', '', html)
        html = re.sub(r'\\huge\s*', '', html)
        html = re.sub(r'\\normalsize\s*', '', html)
        html = re.sub(r'\{([^}]*)\\small([^}]*)\}', r'\1\2', html)  # Remove { \small ... }
        
        # Clean up any remaining LaTeX commands that might have slipped through
        html = re.sub(r'\\begin\{enumerate\}', '', html)
        html = re.sub(r'\\end\{enumerate\}', '', html)
        html = re.sub(r'\\begin\{itemize\}', '', html)
        html = re.sub(r'\\end\{itemize\}', '', html)
        html = re.sub(r'\\begin\{quote\}', '', html)
        html = re.sub(r'\\end\{quote\}', '', html)
        html = re.sub(r'\\begin\{em\}', '', html)
        html = re.sub(r'\\end\{em\}', '', html)
        html = re.sub(r'\\item\s+', '', html)  # Remove any remaining \item commands
        html = re.sub(r'\{[0-9]+pt\}', '', html)  # Remove {20pt} etc
        html = re.sub(r'% Begin compact.*', '', html)  # Remove comments
        html = re.sub(r'\{[^}]*\}', '', html)  # Remove any remaining single braces with content
        
        # Clean up malformed HTML tags
        html = re.sub(r'</ul></div>', '</ul>', html)  # Fix </ul></div> issues
        html = re.sub(r'<ul></div>', '<ul>', html)  # Fix <ul></div> issues
        html = re.sub(r'<div class="ingredient-item"><li>', '<li>', html)  # Fix nested structure
        html = re.sub(r'</li></div>', '</li>', html)  # Fix closing tags
        html = re.sub(r'<div class="ingredient-item"><h4>', '<h4>', html)
        html = re.sub(r'</h4></div>', '</h4>', html)
        html = re.sub(r'<div class="ingredient-item"><ul>', '<ul>', html)
        html = re.sub(r'<div class="ingredient-item"></ul>', '</ul>', html)
        
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
        # Split content by \item, but be careful about the pattern
        # We want to match \item at the start of a line (with optional leading whitespace)
        # or \item with preceding whitespace
        items = []
        
        # Split by \item - this is more reliable than regex matching
        parts = re.split(r'\\item\s+', content)
        
        # First part is usually empty (content before first \item), skip it
        for part in parts[1:]:
            part = part.strip()
            if not part:
                continue
            
            # Remove trailing \\ if present
            part = re.sub(r'\\\\\s*$', '', part)
            
            # Convert nested formatting within the item
            part = self._convert_text_formatting(part)
            
            # Convert non-breaking spaces
            part = re.sub(r'~', '&nbsp;', part)
            
            # Preserve paragraph breaks within items (blank lines become <br><br>)
            part = re.sub(r'\n\s*\n+', '<br><br>', part)
            # Convert single newlines to spaces
            part = re.sub(r'\n', ' ', part)
            
            # Clean up extra spaces but preserve intentional breaks
            part = re.sub(r' +', ' ', part)
            part = re.sub(r' <br><br> ', '<br><br>', part)
            part = part.strip()
            
            if part:
                items.append(part)
        
        if not items:
            return '<ol></ol>'
        
        html = '<ol>\n'
        for item in items:
            html += f'    <li>{item}</li>\n'
        html += '</ol>'
        return html
    
    def _convert_itemize(self, content: str) -> str:
        """Convert itemize environment content to HTML unordered list
        
        Args:
            content: Content between \begin{itemize} and \end{itemize}
            
        Returns:
            str: HTML unordered list
        """
        # Split content by \item
        items = []
        
        # Split by \item - this is more reliable than regex matching
        parts = re.split(r'\\item\s+', content)
        
        # First part is usually empty (content before first \item), skip it
        for part in parts[1:]:
            part = part.strip()
            if not part:
                continue
            
            # Remove trailing \\ if present
            part = re.sub(r'\\\\\s*$', '', part)
            
            # Convert nested formatting within the item
            part = self._convert_text_formatting(part)
            
            # Convert non-breaking spaces
            part = re.sub(r'~', '&nbsp;', part)
            
            # Preserve paragraph breaks within items (blank lines become <br><br>)
            part = re.sub(r'\n\s*\n+', '<br><br>', part)
            # Convert single newlines to spaces
            part = re.sub(r'\n', ' ', part)
            
            # Clean up extra spaces but preserve intentional breaks
            part = re.sub(r' +', ' ', part)
            part = re.sub(r' <br><br> ', '<br><br>', part)
            part = part.strip()
            
            if part:
                items.append(part)
        
        if not items:
            return '<ul></ul>'
        
        html = '<ul>\n'
        for item in items:
            html += f'    <li>{item}</li>\n'
        html += '</ul>'
        return html
    
    def _convert_multicols(self, html: str) -> str:
        """Convert multicols environment to HTML grid
        
        Args:
            html: HTML content with multicols
            
        Returns:
            str: HTML with multicols converted to grid
            
        Note: This handles both ingredient lists (with dotfill) and appendix
        sections (with subsections and itemize environments). Lists are already
        converted to HTML by this point.
        """
        # Find multicols blocks - use non-greedy matching but be careful with nested environments
        pattern = r'\\begin\{multicols\}\{(\d+)\}(.*?)\\end\{multicols\}'
        
        def replace_multicols(match):
            cols = int(match.group(1))
            content = match.group(2)
            
            # Check if this is an ingredient list (has dotfill) or appendix (has HTML h4 tags or ul/ol)
            has_dotfill = '\\dotfill' in content
            has_html_structure = '<h4>' in content or '<ul>' in content or '<ol>' in content or '<li>' in content
            
            if has_html_structure:
                # This is an appendix section - already has HTML structure, just wrap in grid
                # Clean up any remaining LaTeX commands that might be mixed in
                content = re.sub(r'\\setlength\{[^}]+\}', '', content)
                content = re.sub(r'\{[0-9]+pt\}', '', content)  # Remove {20pt} etc
                content = re.sub(r'% Begin compact.*', '', content, flags=re.MULTILINE)  # Remove comments
                content = re.sub(r'\\item\s+', '', content)  # Remove any remaining \item
                content = re.sub(r'\\begin\{itemize\}', '', content)
                content = re.sub(r'\\end\{itemize\}', '', content)
                content = re.sub(r'\\begin\{enumerate\}', '', content)
                content = re.sub(r'\\end\{enumerate\}', '', content)
                # Remove standalone braces that are just LaTeX formatting
                content = re.sub(r'^\{[^}]*\}$', '', content, flags=re.MULTILINE)
                # Clean up any stray } at start of lines
                content = re.sub(r'^\}', '', content, flags=re.MULTILINE)
                return f'<div class="ingredients-columns">{content}</div>'
            
            # This is an ingredient list - process line by line
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
    
    def _convert_nonmulticol_ingredients(self, html: str) -> str:
        """Convert ingredient lists that aren't in multicols environment
        
        Detects ingredient lists that use \dotfill but aren't wrapped in multicols.
        These are typically simple single-column ingredient lists.
        
        Args:
            html: HTML content that may contain non-multicol ingredient lists
            
        Returns:
            str: HTML with non-multicol ingredient lists properly wrapped
        """
        # Pattern to match ingredient sections: <h3>Ingredients</h3> followed by
        # lines with \dotfill and \\ until we hit the next section or other content
        
        def replace_ingredient_section(match):
            section_tag = match.group(1)  # The section tag
            content = match.group(2)  # Content between section and next section
            
            # Check if this content contains ingredient lines (has \dotfill)
            if '\\dotfill' not in content:
                return match.group(0)  # Not an ingredient list, return unchanged
            
            # Check if this is already in a multicols (shouldn't happen, but be safe)
            if '\\begin{multicols}' in content or '<div class="ingredients-columns">' in content:
                return match.group(0)  # Already handled by multicols conversion
            
            # Extract ingredient lines - lines that contain \dotfill followed by \\
            lines = content.split('\n')
            ingredient_lines = []
            other_content = []
            found_ingredients = False
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                
                # Skip empty lines and comments
                if not line_stripped or line_stripped.startswith('%'):
                    if found_ingredients and not other_content:
                        # Still in ingredient block, preserve blank lines
                        ingredient_lines.append('')
                    elif not found_ingredients:
                        other_content.append(line)
                    continue
                
                # Check if this is an ingredient line (has \dotfill and ends with \\)
                # LaTeX line breaks are \\, which in Python strings is represented as '\\\\'
                # We check for \dotfill and if line ends with backslash(es) or contains \\
                is_ingredient_line = '\\dotfill' in line and (line.rstrip().endswith('\\') or '\\\\' in line)
                if is_ingredient_line:
                    found_ingredients = True
                    ingredient_lines.append(line)
                # Check if we've hit the next section or significant content
                elif (line_stripped.startswith('\\section') or 
                      line_stripped.startswith('<h3>') or
                      line_stripped.startswith('<h4>') or
                      line_stripped.startswith('\\begin{enumerate}') or
                      line_stripped.startswith('<ol>') or
                      line_stripped.startswith('\\begin{itemize}') or
                      line_stripped.startswith('<ul>')):
                    # Hit next section or list - everything from here is not ingredients
                    other_content.extend(lines[i:])
                    break
                elif found_ingredients:
                    # We were collecting ingredients, but this line doesn't match
                    # Check if it's just whitespace/formatting or if we should stop
                    # If it has significant content (not just LaTeX commands), stop
                    significant_content = re.sub(r'\\[a-zA-Z]+\{?[^}]*\}?', '', line_stripped)
                    significant_content = re.sub(r'\{[^}]*\}', '', significant_content)
                    if significant_content.strip():
                        # This has real content, stop collecting ingredients
                        other_content.extend(lines[i:])
                        break
                    else:
                        # Just LaTeX formatting, might be part of ingredient block
                        ingredient_lines.append(line)
                else:
                    other_content.append(line)
            
            # If we found ingredient lines, convert them
            if ingredient_lines:
                # Build the ingredient HTML
                grid_html = '<div class="ingredients-columns">\n'
                
                for line in ingredient_lines:
                    line = line.strip()
                    if not line or line.startswith('%'):
                        continue
                    
                    # Remove trailing backslashes (LaTeX line breaks: \\)
                    # Handle both single and double backslashes
                    line = line.rstrip('\\').strip()
                    
                    # Convert LaTeX fraction commands before processing
                    line = re.sub(r'\\textonehalf(\{\})?', '½', line)
                    line = re.sub(r'\\textonequarter(\{\})?', '¼', line)
                    line = re.sub(r'\\textthreequarter(\{\})?', '¾', line)
                    line = re.sub(r'\\textonethird(\{\})?', '⅓', line)
                    line = re.sub(r'\\texttwothirds(\{\})?', '⅔', line)
                    
                    # Split on \dotfill to get name and amount
                    if '\\dotfill' in line:
                        parts = line.split('\\dotfill')
                        if len(parts) == 2:
                            name = parts[0].strip()
                            amount = parts[1].strip()
                            grid_html += f'    <div class="ingredient-item"><span class="ingredient-name">{name}</span><span class="dotfill"></span><span class="ingredient-amount">{amount}</span></div>\n'
                        else:
                            grid_html += f'    <div class="ingredient-item">{line}</div>\n'
                    else:
                        grid_html += f'    <div class="ingredient-item">{line}</div>\n'
                
                grid_html += '</div>\n'
                
                # Reconstruct the section
                other_text = '\n'.join(other_content).strip()
                if other_text:
                    return f'{section_tag}\n{grid_html}{other_text}'
                else:
                    return f'{section_tag}\n{grid_html}'
            
            return match.group(0)  # No ingredient lines found, return unchanged
        
        # Match <h3>Ingredients</h3> followed by content until next section
        # We need to capture everything from <h3>Ingredients</h3> until the next <h3> or other significant tag
        # Use a more explicit pattern that stops at clear boundaries
        pattern = r'(<h3>Ingredients</h3>)(.*?)(?=<h3>|<h4>|\\section|\\begin\{enumerate\}|<ol>|\\begin\{itemize\}|<ul>|$)'
        
        result = re.sub(pattern, replace_ingredient_section, html, flags=re.DOTALL)
        return result


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
        
        # Add custom filter for URL-safe ID generation
        def url_safe_id(text: str) -> str:
            """Convert text to URL-safe ID by removing/replacing special characters"""
            import re
            # Convert to lowercase
            text = text.lower()
            # Replace spaces and underscores with hyphens
            text = re.sub(r'[\s_]+', '-', text)
            # Remove all non-alphanumeric characters except hyphens
            text = re.sub(r'[^a-z0-9\-]', '', text)
            # Remove multiple consecutive hyphens
            text = re.sub(r'-+', '-', text)
            # Remove leading/trailing hyphens
            text = text.strip('-')
            return text
        
        self.jinja_env.filters['url_safe_id'] = url_safe_id
        
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
