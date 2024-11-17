from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import re
from collections import defaultdict
from culinary_data_manager import CulinaryDataManager
from rich.console import Console
from rich.table import Table

"""Cookbook Index Generator

This module processes LaTeX cookbook files to generate comprehensive indexes.

Usage as module:
    from _tools.indexer import CookbookIndexer
    
    indexer = CookbookIndexer()
    indexer.process_cookbook(input_file, output_file)

Usage from command line:
    python _tools/indexer.py
"""

@dataclass
class IndexEntry:
    """Represents a single index entry in the cookbook.
    
    Stores information about where and how a term appears in the cookbook,
    including its context, confidence level, and relationship to recipes.
    
    Attributes:
        term: The indexed term or phrase
        page: Page number where term appears
        category: Classification category (e.g., technique, ingredient)
        context: Surrounding text where term appears
        confidence: Match confidence score (0-1)
        is_recipe_title: Whether this entry is a main recipe heading
        parent_recipe: Name of recipe containing this term, if any
    """
    term: str
    page: int
    category: str
    context: str
    confidence: float
    is_recipe_title: bool = False
    parent_recipe: Optional[str] = None

class CookbookIndexer:
    """Processes cookbook content to generate comprehensive LaTeX indexes.
    
    This class handles the identification of indexable terms in cookbook content
    and generates appropriate LaTeX index commands. It maintains tracking of
    recipe titles, term occurrences, and generates hierarchical index entries.
    
    Key Features:
    - Identifies culinary terms, techniques, and ingredients
    - Tracks recipe titles and their relationships to terms
    - Generates hierarchical index entries with cross-references
    - Supports confidence-based term matching
    - Preserves LaTeX formatting while adding index commands
    
    Attributes:
        entries: Dictionary mapping terms to their index entries
        recipe_titles: Set of identified recipe titles
        confidence_threshold: Minimum confidence for term inclusion
    """
    def __init__(self):
        self.data_manager = CulinaryDataManager()
        self.data_manager.load_all_data()
        
        self.entries: Dict[str, List[IndexEntry]] = defaultdict(list)
        self.recipe_titles: Set[str] = set()
        self.confidence_threshold = 0.6
        
    def process_cookbook(self, input_file: Path, output_file: Path) -> None:
        """Process a LaTeX cookbook file and create an indexed version.
        
        Handles the complete workflow of processing a cookbook file:
        1. Loads and reads the input LaTeX file
        2. Processes content to identify indexable terms
        3. Generates index commands and required LaTeX setup
        4. Writes the indexed version to the output file
        
        Args:
            input_file: Path to source LaTeX cookbook file
            output_file: Path where indexed version should be saved
            
        Raises:
            FileNotFoundError: If input file cannot be opened
            OSError: If output file cannot be written
        """
        # Load the input file
        with open(input_file, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Process the content
        processed_content = self._process_content(content)
        
        # Generate the output
        self._write_output(processed_content, output_file)

    def _process_content(self, content: str) -> str:
        """Process LaTeX content to identify and index terms.
        
        Processes cookbook content line by line to identify indexable terms and add
        appropriate index markup. Handles special cases like recipe titles and 
        ingredient lists.
        
        Args:
            content: Raw LaTeX content from cookbook file
            
        Returns:
            str: Processed content with index markup added
            
        Processing steps:
        1. Track page numbers via \newpage commands
        2. Identify recipe titles from section headings
        3. Process ingredients (marked with \dotfill)
        4. Process regular text for culinary terms
        5. Add index markup while preserving LaTeX formatting
        """
        current_page = 1
        current_recipe = None
        processed_lines = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Track page numbers
            if '\\newpage' in line:
                current_page += 1
                processed_lines.append(line)
                continue
            
            # Process recipe titles (including section* for unnumbered sections)
            recipe_match = re.search(r'\\(?:sub)?section\*?\{([^}]+)\}', line)
            if recipe_match:
                current_recipe = recipe_match.group(1)
                self._process_recipe_title(current_recipe, current_page)
            
            # Process the line for culinary terms
            processed_line = self._process_line(
                line, 
                current_page, 
                current_recipe,
                is_ingredient_list='\\dotfill' in line
            )
            processed_lines.append(processed_line)
        
        return '\n'.join(processed_lines)

    def _process_recipe_title(self, title: str, page: int) -> None:
        """Process a recipe title and create related index entries.
        
        Creates index entries for the recipe title itself and any culinary terms
        found within the title. Recipe titles get special handling with bold page
        numbers and potential hierarchical entries.
        
        Args:
            title: Recipe title text from section heading
            page: Current page number where title appears
            
        Processing steps:
        1. Add title to tracked recipe set
        2. Create primary index entry for recipe (bold page number)
        3. Identify cuisine/dish terms from title
        4. Create hierarchical index entries for identified terms
        """
        self.recipe_titles.add(title)
        
        # Add basic index entry for the recipe
        self.entries[title].append(
            IndexEntry(
                term=title,
                page=page,
                category="recipe",
                context=f"Recipe title: {title}",
                confidence=1.0,
                is_recipe_title=True
            )
        )
        
        # Check for cuisine or dish type terms in title
        matches = self.data_manager.get_term_matches(title)
        for term, confidence in matches:
            if confidence >= self.confidence_threshold:
                term_data = self.data_manager.terms[term]
                self.entries[term].append(
                    IndexEntry(
                        term=term,
                        page=page,
                        category=term_data.category,
                        context=f"Found in recipe title: {title}",
                        confidence=confidence,
                        parent_recipe=title
                    )
                )

    def _clean_latex(self, text: str) -> str:
        """Remove LaTeX commands while preserving the content inside them.
        
        Args:
            text: Raw LaTeX text
            
        Returns:
            str: Cleaned text with commands removed but content preserved
        """
        # Remove comments
        text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
        
        # Replace common LaTeX commands while preserving their content
        text = re.sub(r'\\[a-zA-Z]+(\[.*?\])?{([^{}]*)}', r'\2', text)
        
        # Remove remaining command markers and braces
        text = re.sub(r'\\[a-zA-Z]+', ' ', text)
        text = text.replace('{', ' ').replace('}', ' ')
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text

    def _process_line(self, line: str, page: int, current_recipe: Optional[str], 
                     is_ingredient_list: bool) -> str:
        """Process a single line of text and add index markup.
        
        Analyzes line content for indexable terms and adds appropriate index markup.
        Handles ingredient lines and regular text differently, with special confidence
        handling for explicitly listed ingredients.
        
        Args:
            line: Single line of LaTeX content to process
            page: Current page number being processed
            current_recipe: Name of current recipe section, if any
            is_ingredient_list: True if line contains \dotfill (ingredient line)
            
        Returns:
            str: Line with index markup added
            
        Processing steps:
        1. Skip LaTeX commands and comments
        2. Extract ingredient names from ingredient lines
        3. Match terms with confidence scoring
        4. Create index entries while avoiding overlaps
        5. Preserve original LaTeX formatting
        """
        # Skip processing of LaTeX commands and comments
        if line.strip().startswith('\\') or line.strip().startswith('%'):
            return line
        
        # Clean the line before matching
        clean_line = self._clean_latex(line)
        
        if is_ingredient_list:
            ingredient = clean_line.split('dotfill')[0].strip()  # Note: \dotfill was cleaned
            matches = self.data_manager.get_term_matches(ingredient)
        else:
            # Normal term matching for non-ingredient lines
            matches = self.data_manager.get_term_matches(clean_line)
        
        # Sort matches by confidence
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Track where we've inserted index commands to avoid overlaps
        indexed_positions = set()
        
        # Process each match
        for term, confidence in matches:
            if confidence < self.confidence_threshold:
                continue
                
            term_data = self.data_manager.terms[term]
            
            # Create index entry
            entry = IndexEntry(
                term=term,
                page=page,
                category=term_data.category,
                context=line.strip(),
                confidence=confidence,
                parent_recipe=current_recipe
            )
            
            # Add to entries if not already indexed on this page
            if not any(e.page == page and e.term == term for e in self.entries[term]):
                self.entries[term].append(entry)
                
        return line

    def _generate_index_commands(self) -> List[str]:
        """Generate formatted LaTeX index commands.
        
        Creates properly formatted index commands for all entries, handling special
        cases like recipe titles and hierarchical relationships. Groups entries by
        category for better organization.
        
        Returns:
            List[str]: LaTeX index commands for all processed entries
            
        Generation steps:
        1. Group entries by category
        2. Sort entries within categories
        3. Format commands based on entry type:
           - Bold page numbers for recipe titles
           - Subentries for terms within recipes
           - Standard entries for other terms
        4. Handle special formatting and cross-references
        """
        commands = []
        
        # Group entries by category
        entries_by_category = defaultdict(list)
        for term, entry_list in self.entries.items():
            # Use the highest confidence entry's category
            best_entry = max(entry_list, key=lambda x: x.confidence)
            entries_by_category[best_entry.category].append((term, entry_list))
            
        # Generate commands for each category
        for category, term_entries in entries_by_category.items():
            for term, entries in term_entries:
                # Sort entries by page number
                sorted_entries = sorted(entries, key=lambda x: x.page)
                
                for entry in sorted_entries:
                    if entry.is_recipe_title:
                        # Recipe titles get bold page numbers
                        commands.append(f"\\index{{{category}!{term}|textbf}}")
                    elif entry.parent_recipe:
                        # Entries within recipes get subentries
                        commands.append(
                            f"\\index{{{category}!{term}!{entry.parent_recipe}"
                            f"@\\textit{{{entry.parent_recipe}}}}}"
                        )
                    else:
                        # Regular entries
                        commands.append(f"\\index{{{category}!{term}}}")
                        
        return commands

    def _write_output(self, content: str, output_file: Path) -> None:
        """Write the processed content to the output file.
        
        Generates final LaTeX output by:
        1. Adding required package imports
        2. Inserting index commands after document begin
        3. Adding index printing command at end
        4. Writing complete content to output file
        
        Args:
            content: Processed content with index markup
            output_file: Path where output should be written
            
        Raises:
            OSError: If output file cannot be written
        """
        # Generate index commands
        index_commands = self._generate_index_commands()
        
        # Add required packages and commands
        header = (
            "\\usepackage{makeidx}\n"
            "\\makeindex\n\n"
        )
        
        # Insert index commands after \begin{document}
        modified_content = (
            header
            + content.replace(
                "\\begin{document}",
                "\\begin{document}\n% Auto-generated index commands\n"
                + '\n'.join(index_commands)
            )
            + "\n\\printindex\n"
        )
        
        # Write the output
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(modified_content)
        
        # Print summary after successful write
        self.print_indexing_summary()

    def set_confidence_threshold(self, threshold: float) -> None:
        """Set the confidence threshold for including terms in the index.
        
        Controls term matching sensitivity by setting minimum confidence level
        required for terms to be included in the index.
        
        Args:
            threshold: Float between 0 and 1 representing confidence cutoff
            
        Raises:
            ValueError: If threshold is not between 0 and 1
        """
        if 0 <= threshold <= 1:
            self.confidence_threshold = threshold
        else:
            raise ValueError("Confidence threshold must be between 0 and 1")

    def print_indexing_summary(self) -> None:
        """Print summary of indexing results using rich formatting"""
        console = Console()
        
        # Calculate summary statistics
        total_terms = len(self.entries)
        total_entries = sum(len(entries) for entries in self.entries.values())
        recipe_count = len(self.recipe_titles)
        
        # Print summary statistics
        console.print("\n[bold]Indexing Summary:[/bold]")
        console.print(f"• Total unique terms: {total_terms}")
        console.print(f"• Total index entries: {total_terms}")
        console.print(f"• Recipes indexed: {recipe_count}\n")
        
        # Create category summary table
        category_table = Table(title="Index Categories")
        category_table.add_column("Category", style="cyan")
        category_table.add_column("Terms", justify="right")
        category_table.add_column("Entries", justify="right")
        
        # Group entries by category
        categories = defaultdict(lambda: {"terms": 0, "entries": 0})
        for term, entry_list in self.entries.items():
            # Use the highest confidence entry's category
            best_entry = max(entry_list, key=lambda x: x.confidence)
            categories[best_entry.category]["terms"] += 1
            categories[best_entry.category]["entries"] += len(entry_list)
        
        # Add rows for each category
        for category, counts in sorted(categories.items()):
            category_table.add_row(
                category.title(),
                str(counts["terms"]),
                str(counts["entries"])
            )
        
        console.print(category_table)
        
        # Create recipe index coverage table
        recipe_table = Table(title="\nRecipe Index Coverage")
        recipe_table.add_column("Recipe Title", style="cyan")
        recipe_table.add_column("Terms Found", justify="right")
        recipe_table.add_column("Coverage", justify="center")
        
        # Calculate terms per recipe
        recipe_terms = defaultdict(int)
        for term, entry_list in self.entries.items():
            for entry in entry_list:
                if entry.parent_recipe:
                    recipe_terms[entry.parent_recipe] += 1
        
        # Add rows for each recipe
        for recipe in sorted(self.recipe_titles):
            term_count = recipe_terms[recipe]
            # Simple coverage rating based on number of terms
            coverage = (
                "[green]High[/green]" if term_count > 10
                else "[yellow]Medium[/yellow]" if term_count > 5
                else "[red]Low[/red]"
            )
            recipe_table.add_row(recipe, str(term_count), coverage)
        
        console.print(recipe_table)

def demo_usage():
    """Demonstrate usage of the CookbookIndexer"""
    # Create indexer (no need to create data manager separately)
    indexer = CookbookIndexer()
    
    # Set custom confidence threshold if desired
    indexer.set_confidence_threshold(0.7)
    
    # Process a cookbook
    indexer.process_cookbook(
        Path("my_cookbook.tex"),
        Path("my_cookbook_indexed.tex")
    )

if __name__ == "__main__":
    demo_usage()
