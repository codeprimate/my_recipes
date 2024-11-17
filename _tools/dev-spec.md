# Recipe Book Build System Design Specification

This system was originally conceived to convert a directory of LaTeX recipe files into a compiled recipe book, following "convention over configuration" principles.

My goal is to make this system generic and reusable for other projects.

## System Overview

The build system processes individual LaTeX recipe files into a cohesive book by:
1. Detecting sections from directory structure
2. Extracting content and package requirements
3. Preprocessing content for consistency
4. Assembling and compiling a final book

## Directory Structure
```
.
├── _templates/          
│   └── book.tex        # Single master template for book compilation
├── _tools/             
│   ├── build.py        # Main entry point and orchestration
│   ├── scan.py         # Directory/file scanner
│   ├── extract.py      # Content/package extractor
│   ├── preprocess.py   # Content normalizer
│   ├── compile.py      # Book assembler
│   └── book.yml        # Main configuration
├── _build/             # Build artifacts (git-ignored)
│   ├── metadata.yml    # Build state tracking
│   └── bodies/         # Preprocessed tex content
├── [##-]section_name/  # Content directories
│   └── recipe.tex      # Source files
```

## Conventions

### Directory Names
- Directories starting with `_` are system/build related
- All other directories are automatically detected as book sections
- Optional numeric prefix in directory names (e.g., "01-appetizers")
  - Prefixes are stripped in final output
  - Used only for developer organization
- Directory names are converted to section titles
  - Underscores/hyphens converted to spaces
  - Case properly titleized
- Sections sorted alphabetically in final book

### Source Files
- Each recipe is a complete LaTeX document
- Content between \begin{document} and \end{document} is extracted
- Package requirements are detected and consolidated

## Configuration Files

### _tools/book.yml

Static book definition containing:
```yaml
title: "Family Cookbook"
authorship:
  author: "Your Name"
  version: "2024 Edition"
  copyright: "2024"
template: "book.tex.jinja"
style:
  documentclass: "article"
  size: "letterpaper"
  base_font_size: "11pt"
  twoside: true
  include_toc: true
  include_index: false
  geometry:
    top: 1in
    bottom: 1in
    left: 1.4in
    right: 1.5in
  font:
    family: "Doves Type"
    scale: 1.4
    auto_fake_bold: 1.5
    auto_fake_slant: 0.3
build:
  source: ""
  output_dir: "_build"
```

### _build/metadata.yml

Dynamic build state tracking:

```yaml
# last build timestamp, used to determine if recipes have been updated by comparing source file mtimes
last_build: "2024-03-16T15:30:00Z"
# packages are detected from the recipe source files, and consolidated into a single list
packages:
  - fontspec
  - tocloft
  - multicol
  - graphicx
  - geometry
  - inputenc
# recipe list in no particular order
recipes:
  "01-entrees/pot_roast.tex":
    section: "01-entrees"
    mtime: "2024-03-15T10:20:00Z"
    title: "Classic Pot Roast"
    packages:
      - enumitem
    extracted_body: "_build/bodies/01-entrees/pot_roast.tex"
    preprocessed: true
  "02-desserts/kettle_corn.tex":
    section: "02-desserts"
    mtime: "2024-03-15T10:20:00Z"
    title: "Kettle Corn"
    packages:
      - enumitem
    extracted_body: "_build/bodies/02-desserts/kettle_corn.tex"
    preprocessed: false
  "sides/green_bean_casserole.tex":
    section: "sides"
    mtime: "2024-03-15T10:20:00Z"
    title: "Green Bean Casserole"
    packages:
      - enumitem
    extracted_body: "_build/bodies/sides/green_bean_casserole.tex"
    preprocessed: false
# Section list in order of appearance in book, with titles converted to spaces and titleized
sections:
  "01-entrees": "Entrees"
  "02-desserts": "Desserts and Snacks"
  "sides": "Sides"  
```

## Build Pipeline

### 1. scan.py
- Discovers all tex files in content directories
- Checks modification times against previous build
- Updates metadata with file information
- Ignores system directories (starting with `_` or `.`)
- Provides rich console output with scan summary including:
  - Total sections and recipes
  - Changed recipe count
  - Error tracking
- Maintains metadata structure:
```yaml
last_build: "2024-03-16T15:30:00Z"
recipes:
  "path/to/recipe.tex":
    section: "section_name"
    mtime: "2024-03-15T10:20:00Z"
    title: "Recipe Title"
    packages: []
    extracted_body: false
    preprocessed: false
    changed: true  # Indicates if file changed since last scan
sections:
  "section_dir": "Section Title"
scan_errors:  # Tracks any errors during scanning
  - section: "directory_scan"
    error: "Error message"
    type: "ErrorType"
```

### 2. extract.py
- Extracts content between \begin{document} and \end{document}
- Identifies package requirements from \usepackage statements
- Updates metadata with:
  - List of required packages per recipe
  - Global consolidated package list
  - Path to extracted content file
  - Extraction errors if any occur
- Stores extracted content in _build/bodies/ maintaining source directory structure
- Provides rich console output with extraction summary including:
  - Total recipe count
  - Successfully processed count
  - Error count
  - Detailed tables showing:
    - Recipe processing status
    - Any errors encountered
- Maintains metadata structure:
```yaml
recipes:
  "path/to/recipe.tex":
    packages: []  # List of required packages
    extracted_body: "_build/bodies/path/to/recipe.tex"
packages: []  # Global consolidated package list
extraction_errors:  # Tracks any errors during extraction
  - recipe: "path/to/recipe.tex"
    error: "Error message"
    type: "ErrorType"
```

### 3. preprocess.py
- Normalizes extracted content
- Cleans up formatting
- Prepares content for inclusion in master template
- Updates metadata with preprocessing status

### 4. compile.py
- Reads master template from `_tools/book.tex.jinja`
- Integrates all required packages
- Includes preprocessed content
- Generates final book

### build.py
- Main entry point
- Orchestrates pipeline execution
- Handles errors and logging
- Ensures clean state between runs

## Development Guidelines

1. Each script should be independently runnable
2. Scripts should update metadata.yml with their state
3. Build process should be incremental (only process changed files)
4. All build artifacts go in _build directory
5. Source files remain unchanged
6. Error handling should be clear and actionable

## Usage

Basic build:
```bash
python _tools/build.py
```

Individual steps can be run for development:
```bash
python _tools/scan.py
python _tools/extract.py
python _tools/preprocess.py
python _tools/compile.py
```
