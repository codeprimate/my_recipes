# Recipe Book Builder

A build system that converts a collection of LaTeX recipe files into a beautifully formatted cookbook. Built with a "convention over configuration" philosophy for simplicity and ease of use.

## Features

- Automatically organizes recipes into sections based on directory structure
- Extracts and consolidates LaTeX package requirements
- Supports custom styling and formatting through configuration
- Incremental builds - only processes changed files
- Rich console output with detailed build status
- Generates table of contents and optional index
- **HTML export** - Convert LaTeX cookbook to self-contained HTML with embedded CSS

## Prerequisites

- Python 3.8+
- XeLaTeX compiler (for PDF generation)
- Python packages can be installed via:
  ```bash
  pip install -r requirements.txt
  ```

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/codeprimate/recipe-book-builder.git
   cd recipe-book-builder
   ```

2. Create your recipe directory structure:
 
   ```
   your-cookbook/
   ├── _templates/          
   ├── _tools/             
   │   └── book.yml        # Configure your book settings
   └── recipes/            # Your recipe files go here
       ├── appetizers/
       ├── main-dishes/
       └── desserts/
   ```

3. Configure your book settings in `_tools/book.yml`:

   ```yaml
   title: "Your Cookbook Name"
   authorship:
     author: "Your Name"
     version: "2026 Edition"
   build:
     html_export: true  # Enable HTML export (requires Pandoc)
     html_output_dir: "html"
   ```

## Usage

### Python setup

**TODO**

### Basic Build

To build your cookbook:

```bash
python _tools/build.py
```

The compiled PDF will be created in the `_build` directory.

If HTML export is enabled in your configuration, a self-contained HTML file with embedded CSS will be generated in `_build/html/book.html`.

### Recipe File Structure

Each recipe should be a complete LaTeX document:

```latex
\documentclass{article}
\usepackage{enumitem}

\title{Classic Chocolate Chip Cookies}

\begin{document}
\section*{Ingredients}
\begin{itemize}
  \item 2 1/4 cups flour
  \item 1 cup butter
\end{itemize}

\section*{Instructions}
...
\end{document}
```

### Directory Organization

- Create directories for each section of your cookbook
- Optionally prefix directories with numbers for custom ordering (e.g., "01-appetizers")
- Directory names are automatically converted to section titles
  - `01-main-dishes` → "Main Dishes"
  - `holiday_recipes` → "Holiday Recipes"

### Advanced Usage

Run individual build steps for development:

```bash
python _tools/scan.py      # Scan for recipe files
python _tools/extract.py   # Extract content and requirements
python _tools/preprocess.py # Normalize content
python _tools/compile.py   # Generate final PDF
python _tools/html_export.py  # Export HTML (requires Pandoc)
```

Use a custom config file:

```bash
python _tools/build.py --config path/to/config.yml
```

## Build Output

The system creates a `_build` directory containing:

- Final PDF cookbook (`book.pdf`)
- HTML export (`html/book.html`) - if HTML export is enabled
- Extracted and preprocessed recipe content (`bodies/`)
- Build metadata and logs (`metadata.yml`)

### HTML Export

The HTML export feature generates a single self-contained HTML file with embedded CSS. The styling can be customized by editing the template at `_tools/templates/web/book.html.jinja`.

Features:
- Responsive design (mobile/tablet friendly)
- Print-friendly CSS
- Embedded CSS (no external dependencies)
- Table of contents navigation

## Contributing

Contributions are welcome! Submit pull requests to my repository.

## License

MIT License

Copyright (c) codeprimate 2024-2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.