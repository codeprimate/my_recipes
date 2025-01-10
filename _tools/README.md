# Recipe Book Builder

A build system that converts a collection of LaTeX recipe files into a beautifully formatted cookbook. Built with a "convention over configuration" philosophy for simplicity and ease of use.

## Features

- Automatically organizes recipes into sections based on directory structure
- Extracts and consolidates LaTeX package requirements
- Supports custom styling and formatting through configuration
- Incremental builds - only processes changed files
- Rich console output with detailed build status
- Generates table of contents and optional index

## Prerequisites

- Python 3.8+
- XeLaTeX compiler
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
     version: "2024 Edition"
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
```

Use a custom config file:

```bash
python _tools/build.py --config path/to/config.yml
```

## Build Output

The system creates a `_build` directory containing:

- Final PDF cookbook
- Extracted and preprocessed recipe content
- Build metadata and logs

## Contributing

Contributions are welcome! Submit pull requests to my repository.

## License

MIT License

Copyright (c) codeprimate 2024

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