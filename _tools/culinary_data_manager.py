import re
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
import requests
import spacy
import csv
import json
from collections import defaultdict
import nltk
from nltk.corpus import wordnet as wn
import pandas as pd
from urllib.request import urlretrieve
import zipfile
import io
import pickle
from tqdm import tqdm
import subprocess
import sys

@dataclass
class CulinaryTerm:
    """Represents a culinary term and its associated metadata.
    
    Stores comprehensive information about a culinary term including its
    variations, categorization, and confidence level in the classification.
    
    Attributes:
        name: Base form of the culinary term
        category: Classification (e.g., ingredient, technique, equipment)
        variations: Alternative forms or spellings of the term
        related_terms: Semantically related culinary terms
        confidence: Classification confidence score (0-1)
    """
    name: str
    category: str
    variations: List[str]
    related_terms: List[str]
    confidence: float = 1.0

class CulinaryDataManager:
    """Manages comprehensive culinary terminology data from multiple sources.
    
    This class handles the loading, processing, and querying of culinary terms
    from various data sources including USDA database and WordNet. It uses
    NLP techniques to enhance term recognition and categorization.
    
    Key Features:
    - Loads and processes USDA food database
    - Extracts culinary terms from WordNet
    - Uses spaCy for NLP-based term enhancement
    - Generates term variations and related terms
    - Provides confidence-scored term matching
    
    Attributes:
        terms: Dictionary mapping term names to CulinaryTerm objects
        nlp: spaCy NLP model for text processing
    """
    
    def __init__(self):
        """Initialize the manager and required NLP components."""
        self.terms: Dict[str, CulinaryTerm] = {}
        
        # Load spaCy model, downloading if needed
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading required spaCy language model...")
            subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
                
        self.cache_file = Path("_build/culinary_data.pkl")
        
        # Download required NLTK data if needed
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            print("Downloading required NLTK data...")
            nltk.download('wordnet')
            nltk.download('omw-1.4')

    def load_all_data(self):
        """Load and process all available culinary data sources."""
        if self._load_cached_data():
            print("✓ Loaded cached culinary data")
            return
            
        print("Building culinary database...")
        self.load_usda_data()
        self.load_wordnet_data()
        self.enhance_with_nlp()
        self._save_cached_data()
        print("✓ Build complete")

    def _load_cached_data(self) -> bool:
        """Load cached culinary data if available.
        
        Returns:
            bool: True if cached data was loaded successfully
        """
        if not self.cache_file.exists():
            return False
            
        try:
            with open(self.cache_file, 'rb') as f:
                self.terms = pickle.load(f)
            return True
        except Exception as e:
            print(f"Warning: Failed to load cached data: {e}")
            return False

    def _save_cached_data(self):
        """Save culinary data to cache file."""
        self.cache_file.parent.mkdir(exist_ok=True)
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.terms, f)
            print(f"Cached culinary data saved to {self.cache_file}")
        except Exception as e:
            print(f"Warning: Failed to save cached data: {e}")

    def load_usda_data(self):
        """Load and process the USDA food database."""
        USDA_URL = "https://fdc.nal.usda.gov/fdc-datasets/Foundation.csv.zip"
        
        try:
            print("Downloading USDA database...")
            response = requests.get(USDA_URL)
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                with z.open('food.csv') as f:
                    df = pd.read_csv(f)
            
            # Progress bar for long-running food processing
            for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing USDA foods"):
                name = row['description'].lower()
                self.terms[name] = CulinaryTerm(
                    name=name,
                    category='ingredient',
                    variations=self._generate_variations(name),
                    related_terms=[],
                    confidence=0.9
                )
                
        except Exception as e:
            print(f"\n⚠️  Error loading USDA data: {e}")
            print("Falling back to basic ingredient list...")
            self._load_fallback_ingredients()

    def load_wordnet_data(self):
        """Load culinary terms from WordNet lexical database."""
        synsets = [
            (wn.synset('food.n.01'), 'ingredient'),
            (wn.synset('cooking.n.01'), 'technique'),
            (wn.synset('utensil.n.01'), 'equipment')
        ]
        
        for synset, category in tqdm(synsets, desc="Processing WordNet terms", ncols=80):
            self._process_synset_hierarchy(synset, category)

    def _process_synset_hierarchy(self, synset, category: str, depth: int = 3):
        """Process a WordNet synset and its hyponyms recursively.
        
        Traverses the WordNet hierarchy to extract culinary terms and their
        relationships, limiting depth to prevent excessive generalization.
        
        Args:
            synset: WordNet synset to process
            category: Classification category for terms
            depth: Maximum recursion depth (default: 3)
            
        Note:
            Skips terms already loaded from USDA to avoid duplicates
        """
        if depth == 0:
            return
        
        # Process current synset
        for lemma in synset.lemmas():
            name = lemma.name().lower().replace('_', ' ')
            
            # Skip if we already have this term from USDA (preferred source)
            if name in self.terms:
                continue
                
            # Get variations and related terms
            variations = self._get_wordnet_variations(lemma)
            related = self._get_wordnet_related_terms(lemma)
            
            self.terms[name] = CulinaryTerm(
                name=name,
                category=category,
                variations=variations,
                related_terms=related,
                confidence=0.7  # Lower confidence for WordNet data
            )
        
        # Process hyponyms
        for hyponym in synset.hyponyms():
            self._process_synset_hierarchy(hyponym, category, depth - 1)

    def enhance_with_nlp(self):
        """Use spaCy to enhance term recognition and categorization."""
        # Progress bar for long-running NLP processing
        for term_name, term_data in tqdm(self.terms.items(), desc="Enhancing terms with NLP"):
            doc = self.nlp(term_name)
            
            chunks = [chunk.text.lower() for chunk in doc.noun_chunks]
            entities = [ent.text.lower() for ent in doc.ents]
            
            new_variations = set(chunks + entities) - {term_name}
            term_data.variations.extend(list(new_variations))
            
            if doc.has_vector:
                category_confidence = self._calculate_category_confidence(doc)
                term_data.confidence = (term_data.confidence + category_confidence) / 2

    def _calculate_category_confidence(self, doc) -> float:
        """Calculate confidence score for category assignment.
        
        Uses word vector similarity between terms and category prototypes
        to validate and score category assignments.
        
        Args:
            doc: spaCy Doc object for the term
            
        Returns:
            float: Confidence score between 0 and 1
            
        Note:
            Requires terms and prototypes to have valid word vectors
        """
        # Prototype terms for each category
        prototypes = {
            'ingredient': ['food', 'ingredient', 'vegetable', 'meat'],
            'technique': ['cook', 'bake', 'fry', 'roast'],
            'equipment': ['pot', 'pan', 'knife', 'bowl']
        }
        
        max_similarity = 0
        for category, terms in prototypes.items():
            for term in terms:
                term_doc = self.nlp(term)
                if term_doc.has_vector and doc.has_vector:
                    similarity = doc.similarity(term_doc)
                    max_similarity = max(max_similarity, similarity)
                    
        return max_similarity

    def _generate_variations(self, term: str) -> List[str]:
        """Generate morphological and semantic variations of a term.
        
        Creates common variations of culinary terms:
        1. Removes common prefixes (fresh, raw, cooked, dried)
        2. Handles plural/singular forms
        3. Adds common modifiers (fresh, cooked)
        
        Args:
            term: Base term to generate variations for
            
        Returns:
            List of unique variations, excluding the original term
        """
        variations = set()
        
        # Remove common suffixes and prefixes
        base_term = re.sub(r'^(fresh |raw |cooked |dried )', '', term)
        base_term = re.sub(r'(s|es|ies)$', '', base_term)
        
        # Add common variations
        variations.add(base_term)
        variations.add(base_term + 's')  # plural
        variations.add('fresh ' + base_term)
        variations.add('cooked ' + base_term)
        
        return list(variations - {term})  # Exclude the original term

    def _get_wordnet_variations(self, lemma) -> List[str]:
        """Extract term variations from WordNet relationships.
        
        Generates variations using WordNet's lexical relationships:
        1. Synonyms from the term's synset
        2. Derivationally related forms
        
        Args:
            lemma: WordNet lemma object
            
        Returns:
            List of unique variations, excluding the original term
            
        Note:
            Handles underscore replacement for multi-word terms
        """
        variations = set()
        
        # Get synonyms
        for syn in lemma.synset().lemmas():
            variations.add(syn.name().lower().replace('_', ' '))
            
        # Get derivationally related forms
        for related_form in lemma.derivationally_related_forms():
            variations.add(related_form.name().lower().replace('_', ' '))
            
        return list(variations - {lemma.name().lower().replace('_', ' ')})

    def _get_wordnet_related_terms(self, lemma) -> List[str]:
        """Extract semantically related terms from WordNet.
        
        Finds related terms using WordNet's semantic relationships:
        1. Terms from similar synsets
        2. Terms with similar meanings or usage
        
        Args:
            lemma: WordNet lemma object
            
        Returns:
            List of unique related terms
            
        Note:
            Focuses on culinary-relevant relationships
        """
        related = set()
        
        # Get terms from similar synsets
        for similar in lemma.synset().similar_tos():
            for sim_lemma in similar.lemmas():
                related.add(sim_lemma.name().lower().replace('_', ' '))
                
        return list(related)

    def _categorize_usda_food(self, row) -> str:
        """Categorize USDA food item into internal taxonomy.
        
        Maps USDA food categories to internal classification system.
        Currently simplified to always return 'ingredient'.
        
        Args:
            row: DataFrame row containing USDA food data
            
        Returns:
            str: Category classification
            
        Todo:
            Implement proper mapping using USDA's categorization fields
        """
        # This would use the USDA food category fields to determine our category
        return 'ingredient'  # Simplified - would normally use USDA's categorization

    def _load_fallback_ingredients(self):
        """Load basic ingredient list as fallback data source.
        
        Provides minimal working dataset when USDA data is unavailable:
        1. Basic cooking ingredients (salt, pepper, etc.)
        2. Common variations of each ingredient
        3. High confidence scores (1.0) for reliability
        
        Note:
            Used as emergency fallback only when USDA load fails
        """
        basic_ingredients = {
            "salt": ["table salt", "sea salt"],
            "pepper": ["black pepper", "white pepper"],
            "flour": ["all-purpose flour", "wheat flour"],
            "sugar": ["granulated sugar", "white sugar"],
            "water": [],
            "oil": ["vegetable oil", "cooking oil"],
        }
        
        for name, variations in basic_ingredients.items():
            self.terms[name] = CulinaryTerm(
                name=name,
                category="ingredient",
                variations=variations,
                related_terms=[],
                confidence=1.0
            )

    def get_term_matches(self, text: str) -> List[Tuple[str, float]]:
        """Find all matching culinary terms in text with confidence scores.
        
        Identifies culinary terms and their variations within the input text,
        calculating confidence scores based on match type and term data.
        
        Args:
            text: Input text to search for culinary terms
            
        Returns:
            List of tuples containing (term_name, confidence_score)
            
        Note:
            Variations of terms receive slightly lower confidence (0.9x)
        """
        matches = []
        doc = self.nlp(text.lower())
        
        # Check each term and its variations
        for term_name, term_data in self.terms.items():
            all_forms = [term_name] + term_data.variations
            for form in all_forms:
                if form in text.lower():
                    matches.append((
                        term_name,
                        term_data.confidence * (1.0 if form == term_name else 0.9)
                    ))
                    
        return matches

def demo_usage():
    """Demonstrate usage of the CulinaryDataManager"""
    manager = CulinaryDataManager()
    manager.load_all_data()
    
    # Test with a sample recipe text
    sample_text = """
    To make this fresh pasta sauce, heat olive oil in a large pan. 
    Add diced tomatoes and minced garlic. 
    Simmer until the sauce thickens.
    """
    
    matches = manager.get_term_matches(sample_text)
    for term, confidence in matches:
        print(f"Found '{term}' with confidence {confidence:.2f}")
        term_data = manager.terms[term]
        print(f"  Category: {term_data.category}")
        print(f"  Variations: {term_data.variations}")
        print(f"  Related terms: {term_data.related_terms}")
        print()

if __name__ == "__main__":
    demo_usage()
