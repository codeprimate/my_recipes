# Recipe Book Build System Design Specification

This system was originally conceived to convert a directory of LaTeX recipe files into a compiled recipe book, following "convention over configuration" principles.

My goal is to make this system generic and reusable for other projects.

## System Overview

The build system processes individual LaTeX recipe files into a cohesive book by:
1. Detecting sections from directory structure
2. Extracting content and package requirements
3. Preprocessing content for consistency
4. Assembling and compiling a final book (PDF)
5. Optionally exporting to HTML format with embedded CSS (using custom LaTeX-to-HTML converter)
6. Copying final outputs to project root

## Directory Structure
```
.
├── _templates/          
│   └── misc.tex        # misc recipe templates
├── _tools/             
│   ├── build.py        # Main entry point and orchestration
│   ├── scan.py         # Directory/file scanner
│   ├── extract.py      # Content/package extractor
│   ├── preprocess.py   # Content normalizer
│   ├── compile.py      # Book assembler (PDF)
│   ├── html_export.py   # HTML exporter
│   ├── book.tex.jinja  # Master LaTeX template (jinja2)
│   ├── templates/
│   │   └── web/
│   │       └── book.html.jinja  # HTML template with embedded CSS
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
- Sections sorted by numeric prefix (if present), then alphabetically
  - Sections with numeric prefixes (e.g., "01-appetizers") sort before those without
  - Within numbered sections, sorted by prefix number
  - Unnumbered sections sort after numbered sections alphabetically

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
  documentclass: "book"  # or "article"
  size: "letterpaper"
  base_font_size: "11pt"
  html_font_size: "14pt"  # Font size for HTML output
  twoside: true
  include_toc: true
  include_index: false
  geometry:
    top: 1in
    bottom: 1in
    left: 1.3in
    right: 1.3in
  font:
    family: "Doves Type"
    scale: 1.2
    auto_fake_bold: 1.5
    auto_fake_slant: 0.3
build:
  source: ""  # Optional source directory override
  output_dir: "_build"  # Build directory for all artifacts
  html_export: true  # Enable HTML export (uses custom converter, no external dependencies)
  html_output_dir: "html"  # Subdirectory for HTML output
latex_compiler: "xelatex"  # LaTeX compiler to use (xelatex or pdflatex)
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
    extracted_body: "bodies/01-entrees/pot_roast.tex"  # Relative to build_dir
    preprocessed: true
    changed: false  # Indicates if file changed since last scan
  "02-desserts/kettle_corn.tex":
    section: "02-desserts"
    mtime: "2024-03-15T10:20:00Z"
    title: "Kettle Corn"
    packages:
      - enumitem
    extracted_body: "bodies/02-desserts/kettle_corn.tex"
    preprocessed: false
    changed: true
  "sides/green_bean_casserole.tex":
    section: "sides"
    mtime: "2024-03-15T10:20:00Z"
    title: "Green Bean Casserole"
    packages:
      - enumitem
    extracted_body: "bodies/sides/green_bean_casserole.tex"
    preprocessed: false
    changed: false
# Section list in order of appearance in book, with titles converted to spaces and titleized
sections:
  "01-entrees": "Entrees"
  "02-desserts": "Desserts and Snacks"
  "sides": "Sides"  
```

## Helper Modules

### helpers.py
Provides shared functionality used across all build stages:
- `load_config(config_path)`: Loads and validates book.yml configuration
  - Validates required sections: title, authorship, template, style, build
  - Returns validated configuration dictionary
  - Raises `FileNotFoundError` or `ValueError` on invalid config
- `load_metadata(metadata_path)`: Loads or creates build metadata
  - Returns existing metadata if file exists and is valid
  - Returns empty metadata structure if file missing or corrupted
  - All file operations use UTF-8 encoding

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
- Extracts recipe title from \title{} command if present
- Updates metadata with:
  - List of required packages per recipe
  - Global consolidated package list
  - Path to extracted content file
  - Recipe title
  - Extraction errors if any occur
- Stores extracted content in _build/bodies/ maintaining source directory structure
- Provides rich console output with extraction summary including:
  - Total recipe count
  - Successfully processed count
  - Error count
  - Detailed tables showing:
    - Recipe processing status by section
    - Any errors encountered with type and message
- Inserts dinkus before `\newpage` commands in recipe bodies
- Maintains metadata structure:
```yaml
recipes:
  "path/to/recipe.tex":
    packages: []  # List of required packages
    extracted_body: "bodies/path/to/recipe.tex"  # Relative to build_dir
    title: "Recipe Title"  # Extracted from \title{} command or filename
    changed: true  # Set during scan stage
packages: []  # Global consolidated package list (updated during extraction)
extraction_errors:  # Tracks any errors during extraction
  - recipe: "path/to/recipe.tex"
    error: "Error message"
    type: "ErrorType"
```

### 3. preprocess.py
- Normalizes extracted content
- Removes layout commands that are handled by master template:
  - `\maketitle` (handled by template)
  - `\thispagestyle{empty}` (handled by template)
- Cleans up formatting inconsistencies
- Prepares content for inclusion in master template
- Updates metadata with preprocessing status (`preprocessed: true`)
- Only processes recipes that haven't been preprocessed yet (incremental)
- Provides rich console output with preprocessing summary

### 4. compile.py
- Reads master template from `_tools/book.tex.jinja`
- Validates build state and dependencies
- Consolidates required LaTeX packages from all recipes
- Adds template-required packages: fontspec, geometry, titlesec, fancyhdr, afterpage
- Adds optional packages based on config: tocloft (if TOC enabled), makeidx (if index enabled)
- Prepares template variables including:
  - Book metadata (title, author, date formatted from last_build)
  - Style configuration (geometry, fonts, document class options)
  - Recipe content organized by section (sorted by title within sections)
  - Recently modified recipes (this month and last month) for optional REVISIONS appendix
  - Twoside flag for two-sided document handling
  - Index flag for index generation
- Renders Jinja2 template with strict whitespace control (`trim_blocks=True`, `lstrip_blocks=True`)
- Template structure:
  - Document preamble with package loading
  - Title page with copyright
  - Table of contents (if enabled)
  - Chapter sections for each recipe category
  - Individual recipes with proper page breaks
  - REVISIONS appendix (if recently modified recipes exist)
- Generates index if configured (currently disabled in implementation)
- Runs specified LaTeX compiler (xelatex or pdflatex) twice for TOC/references
- Cleans up auxiliary LaTeX files (.aux, .log, .toc, .out, .sty)
- Provides detailed compilation summary including:
  - Recipe inclusion status by section
  - Package usage statistics
  - Compilation errors with phase tracking
  - Output file location

### 5. html_export.py (Optional)
- Validates build state and preprocessed recipe content
- Converts LaTeX recipe bodies to HTML using custom `LaTeXToHTMLConverter`:
  - Converts LaTeX commands to HTML equivalents:
    - `\textbf{}` → `<strong>`
    - `\textit{}` / `\emph{}` → `<em>`
    - `\section{}` → `<h3>`
    - `\subsection{}` → `<h4>`
    - `\begin{enumerate}` → `<ol>`
    - `\begin{itemize}` → `<ul>`
    - `\begin{multicols}` → CSS grid layout
    - `\dotfill` → CSS-based dotted line
    - `\nicefrac{n}{d}` → Unicode fractions or HTML sup/sub
    - `\newpage` → `<div class="page-break">`
    - Handles nested formatting and complex structures
  - Preserves recipe structure and formatting
  - Removes LaTeX-specific layout commands
- Prepares template variables (same structure as compile.py)
- Renders HTML template (`_tools/templates/web/book.html.jinja`) with:
  - Book metadata (title, author, etc)
  - Style configuration
  - Embedded CSS styling (responsive design with print styles)
  - HTML-converted recipe content
  - Sticky navigation sidebar with active state tracking (JavaScript-based)
  - Table of contents with anchor links
  - Responsive layout (hides sidebar on mobile, shows on desktop)
  - Print-optimized styles (hides navigation, adjusts layout)
- HTML template structure:
  - Embedded CSS in `<style>` tag (self-contained, no external dependencies)
  - Title page with external links (PDF version, repository)
  - Table of contents (if enabled) with two-column layout
  - Recipe sections with proper heading hierarchy
  - JavaScript for smooth scrolling and active navigation state
  - Columnar ingredient grid layout using CSS Grid
- Generates self-contained HTML file with embedded CSS
- Provides export summary with error reporting
- HTML export errors do not fail the build (non-blocking)
- No external dependencies required (pure Python implementation)

### build.py
- Main entry point and orchestration
- Executes build pipeline in sequence:
  1. Scan content directories
  2. Extract recipe content and packages
  3. Preprocess content
  4. Compile PDF book
  5. Export HTML (if enabled)
  6. Copy outputs to project root (book.pdf, book.html)
- Handles errors and logging at each stage
- Tracks build timing for each stage
- Supports `--clean` flag to force full rebuild
- Provides comprehensive build summary with:
  - Total build duration
  - Stage-by-stage timing
  - Output file locations
  - Error summary by stage
- Stops pipeline on critical errors (HTML export errors are non-blocking)

## Key Features

### Recently Modified Recipes
- Tracks recipes modified in current month and previous month
- Automatically generates REVISIONS appendix in PDF output
- Shows recipe title and formatted modification date
- Only appears if there are recipes modified in the tracked periods

### Incremental Builds
- Only processes recipes that have changed since last build
- Tracks file modification times in metadata
- Preserves existing metadata for unchanged files
- Significantly speeds up rebuilds for large recipe collections

### Error Handling
- Each stage collects errors in structured format:
  ```python
  {
    'phase': 'stage_name',  # e.g., 'validation', 'extraction', 'template'
    'recipe': 'path/to/recipe.tex',  # Optional, if recipe-specific
    'error': 'Error message',
    'type': 'ErrorType'  # Optional error type classification
  }
  ```
- Errors are non-blocking where appropriate (e.g., HTML export)
- Rich console output provides detailed error tables
- Build continues through non-critical errors

## Development Guidelines

1. Each script should be independently runnable with command-line arguments
2. Scripts should update metadata.yml with their state
3. Build process should be incremental (only process changed files)
4. All build artifacts go in _build directory
5. Source files remain unchanged
6. Error handling should be clear and actionable
7. Rich console output should provide clear status and error information
8. Use Jinja2 with strict whitespace control (`trim_blocks=True`, `lstrip_blocks=True`)
9. All file operations use UTF-8 encoding
10. Path handling should be robust (use `pathlib.Path` for cross-platform compatibility)

## Usage

Basic build:
```bash
python _tools/build.py [--config path/to/config]
```

Individual steps can be run for development:
```bash
python _tools/scan.py [--config path/to/config]
python _tools/extract.py [--config path/to/config]
python _tools/preprocess.py [--config path/to/config]
python _tools/compile.py [--config path/to/config]
python _tools/html_export.py [--config path/to/config]  # No external dependencies
```

Build with clean (forces full rebuild):
```bash
python _tools/build.py [--config path/to/config] [--clean]
```
