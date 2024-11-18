from pathlib import Path
import re
from typing import Dict, Set, List
import spacy
from dataclasses import dataclass

@dataclass
class IndexEntry:
    term: str
    pages: Set[int]
    frequency: int = 0

class CookbookIndexer:
    def __init__(self, source_path: Path):
        self.source_path = source_path
        self.output_path = source_path.parent / f"{source_path.stem}.idx"
        # Load the largest, most accurate English model
        try:
            self.nlp = spacy.load("en_core_web_trf")
            print("Using transformer-based model for best accuracy")
        except OSError:
            print("Transformer model not found, falling back to large model")
            try:
                self.nlp = spacy.load("en_core_web_lg")
                print("Using large statistical model")
            except OSError:
                print("Large model not found, falling back to basic model")
                self.nlp = spacy.load("en_core_web_sm")
        
        self.index_entries: Dict[str, IndexEntry] = {}
        
    def is_food_term(self, doc_or_span) -> bool:
        """
        Enhanced food term detection using multiple signals.
        """
        # Expand food-related words for better matching
        FOOD_INDICATORS = {
            'sauce', 'soup', 'stew', 'dish', 'recipe', 'meal', 'ingredient',
            'vegetable', 'fruit', 'meat', 'spice', 'herb', 'seasoning',
            'bread', 'pasta', 'rice', 'cheese', 'fish', 'chicken', 'beef',
            'pork', 'oil', 'butter', 'cream', 'milk', 'flour', 'sugar',
            'salt', 'pepper', 'garlic', 'onion', 'tomato', 'potato'
        }
        
        text = doc_or_span.text.lower()
        
        # Relax the similarity threshold
        if hasattr(self.nlp.vocab, 'similarity'):
            food_terms = ['food', 'ingredient', 'meal', 'cooking']
            similarities = [doc_or_span.similarity(self.nlp(term)) for term in food_terms]
            if max(similarities, default=0) > 0.4:  # Lower threshold from 0.6
                return True

        # Check for food indicators in text
        if any(indicator in text for indicator in FOOD_INDICATORS):
            return True
            
        # Check for explicit food entities
        if any(ent.label_ in {'FOOD', 'PRODUCT', 'ORG'} for ent in doc_or_span.ents):
            return True
        
        return False

    def clean_term(self, term: str) -> str:
        """Clean and normalize food terms."""
        # Remove quantities and units but preserve important measurements
        term = re.sub(r'\b\d+(\s*\/\s*\d+)?(\s*(oz|lb|g|kg|ml|l|cup|tbsp|tsp|pound|ounce)s?\b)?', '', term)
        # Expand prep instructions to remove
        term = re.sub(r'\b(chopped|diced|sliced|minced|crushed|peeled|grated|ground|mashed|cooked)\b', '', term)
        # Remove articles and common prepositions
        term = re.sub(r'\b(a|an|the|of|with|for|in|on|at)\b', '', term)
        # Clean up whitespace and normalize
        term = ' '.join(term.lower().split())
        return term.strip()

    def extract_potential_terms(self, text: str) -> List[tuple[str, float]]:
        """
        Extract potential food terms from text using NLP.
        Returns terms with confidence scores.
        """
        print(f"\nProcessing text: {text[:100]}...")  # Show first 100 chars
        doc = self.nlp(text)
        terms = {}
        
        # Process named entities
        print("\nNamed entities found:")
        for ent in doc.ents:
            print(f"- Entity: {ent.text} (Label: {ent.label_})")
            if ent.label_ in {'FOOD', 'PRODUCT', 'FAC'}:
                cleaned_term = self.clean_term(ent.text)
                if cleaned_term:
                    terms[cleaned_term] = max(terms.get(cleaned_term, 0), 0.9)
                    print(f"  → Added term: {cleaned_term} (conf: 0.9)")

        # Process noun chunks
        print("\nNoun chunks found:")
        for chunk in doc.noun_chunks:
            print(f"- Chunk: {chunk.text}")
            if len(chunk) > 4:
                print("  → Skipped (too long)")
                continue
            
            confidence = 0.0
            
            # Check if it's a food term
            is_food = self.is_food_term(chunk)
            print(f"  → Is food term: {is_food}")
            if is_food:
                confidence = max(confidence, 0.8)
                
                # Add the cleaned term to our terms dictionary
                cleaned_term = self.clean_term(chunk.text)
                if cleaned_term:
                    terms[cleaned_term] = max(terms.get(cleaned_term, 0), confidence)
                    print(f"  → Added term: {cleaned_term} (conf: {confidence})")

        return [(term, conf) for term, conf in terms.items()]

    def process_tex_content(self, content: str):
        """Process TeX content and extract food terms with line numbers."""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Specifically look for ingredient lines and recipe titles
            if any(cmd in line for cmd in [r'\ingredient', r'\item', r'\recipe', r'\section']):
                # Clean TeX commands but preserve content
                cleaned_line = re.sub(r'\\(ingredient|item|recipe|section){([^}]*)}', r'\2', line)
                cleaned_line = re.sub(r'[\\{}]', ' ', cleaned_line)
                
                if cleaned_line.strip():
                    terms = self.extract_potential_terms(cleaned_line)
                    
                    for term, confidence in terms:
                        # Lower confidence threshold
                        if confidence > 0.4:  # Changed from 0.6
                            if term not in self.index_entries:
                                self.index_entries[term] = IndexEntry(term, set(), 0)
                            self.index_entries[term].pages.add(i)
                            self.index_entries[term].frequency += 1

    def generate_index(self):
        """Generate the index file with frequency-based filtering."""
        content = self.read_tex_source()
        self.process_tex_content(content)
        
        # Filter out likely false positives based on frequency
        filtered_entries = {
            term: entry 
            for term, entry in self.index_entries.items() 
            if entry.frequency > 1  # Require at least 2 occurrences
        }
        
        # Write sorted index entries
        with self.output_path.open('w', encoding='utf-8') as f:
            for term in sorted(filtered_entries.keys()):
                pages = sorted(filtered_entries[term].pages)
                pages_str = ", ".join(str(p) for p in pages)
                f.write(f"\\indexentry{{{term}}}{{{pages_str}}}\n")
                
    def read_tex_source(self) -> str:
        """Read the TeX source file."""
        try:
            return self.source_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return self.source_path.read_text(encoding='latin-1')

    def process(self):
        """Main processing method with enhanced reporting."""
        try:
            self.generate_index()
            print(f"Index generated successfully at {self.output_path}")
            print(f"Processed {len(self.index_entries)} unique food terms")
            
            # Report statistics
            confidence_levels = {
                'High': sum(1 for e in self.index_entries.values() if e.frequency > 3),
                'Medium': sum(1 for e in self.index_entries.values() if 2 <= e.frequency <= 3),
                'Low': sum(1 for e in self.index_entries.values() if e.frequency == 1)
            }
            print("\nTerm confidence distribution:")
            for level, count in confidence_levels.items():
                print(f"{level}: {count} terms")
                
        except Exception as e:
            print(f"Error generating index: {e}")

