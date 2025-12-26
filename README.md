# My Recipes

A personal collection of recipes and the toolchain I built to organize and compile them into a beautiful cookbook.

## What's Here

This repository contains two main components:

### Recipe Collection

A curated collection of recipes organized by category:
- **Appetizers** - Starters and small plates
- **Breads and Pastries** - Baked goods and desserts
- **Breakfast** - Morning meals
- **Entrees** - Main dishes
- **Sauces and Seasonings** - Condiments and spice blends
- **Sides** - Accompaniments
- **Snacks** - Quick bites
- **Soups** - Hearty soups and stews

Each recipe is provided in both LaTeX (`.tex`) and PDF formats for easy viewing and compilation.

### Recipe Book Builder Toolchain

A Python-based build system that converts a collection of LaTeX recipe files into a beautifully formatted cookbook. The toolchain follows a "convention over configuration" philosophy for simplicity.

**Key Features:**
- Automatically organizes recipes into sections based on directory structure
- Extracts and consolidates LaTeX package requirements
- Supports custom styling and formatting through configuration
- Incremental builds - only processes changed files
- Generates table of contents and optional index
- **HTML export** - Convert LaTeX cookbook to self-contained HTML with embedded CSS
- Rich console output with detailed build status

For detailed information about the toolchain, see [`_tools/README.md`](_tools/README.md) and [`_tools/dev-spec.md`](_tools/dev-spec.md).

## Quick Start

### Building the Cookbook

1. Install dependencies:
   ```bash
   pip install -r _tools/requirements.txt
   ```

2. Configure your book settings in `_tools/book.yml`

3. Build the cookbook:
   ```bash
   python _tools/build.py
   ```

The compiled PDF will be created in `_build/book.pdf`, and if HTML export is enabled, you'll also get `_build/html/book.html`.

### Using Your Own Recipes

To use this toolchain with your own recipes:

1. Create recipe directories (e.g., `appetizers/`, `main-dishes/`, `desserts/`)
2. Add LaTeX recipe files (`.tex`) to these directories
3. Configure `_tools/book.yml` with your book title and author information
4. Run `python _tools/build.py`

Each recipe should be a complete LaTeX document. See the existing recipes for examples of the format.

## License

### Recipes

Individual recipes are licensed under **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**.

This means:
- **You may share** - Copy and redistribute the material in any medium or format
- **You may adapt** - Remix, transform, and build upon the material
- **Attribution required** - You must give appropriate credit, provide a link to the license, and indicate if changes were made
- **Non-commercial use only** - You may not use the material for commercial purposes

**See [`LICENSE-RECIPES.md`](LICENSE-RECIPES.md) for full license text.**

### Toolchain

The recipe book builder toolchain (`_tools/` directory) is licensed under **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**.

This means:
- **You may share** - Copy and redistribute the material in any medium or format
- **You may adapt** - Remix, transform, and build upon the material
- **Attribution required** - You must give appropriate credit, provide a link to the license, and indicate if changes were made
- **ShareAlike** - If you remix, transform, or build upon the material, you must distribute your contributions under the same license
- **Non-commercial use only** - You may not use the material for commercial purposes

**See [`LICENSE-TOOLS.md`](LICENSE-TOOLS.md) for full license text.**

## Contributing

Contributions are welcome! We accept pull requests for:

### Recipe Submissions and Modifications

- **New recipes** - Submit your favorite recipes in LaTeX format
- **Recipe improvements** - Suggest modifications, corrections, or improvements to existing recipes
- **Recipe formatting** - Help improve consistency and formatting

**Guidelines for recipe contributions:**
- Follow the existing LaTeX recipe format (see existing recipes for examples)
- Place recipes in the appropriate category directory
- Include both `.tex` source and compiled `.pdf` files
- Ensure recipes are complete with ingredients and instructions
- Test that your recipe compiles correctly with the build system

### Toolchain Improvements

- Bug fixes and feature enhancements
- Documentation improvements
- Code quality improvements
- Performance optimizations

**How to contribute:**
1. Fork the repository
2. Create a feature branch for your changes
3. Make your changes
4. Submit a pull request with a clear description of what you've added or modified

## Author

Patrick Morgan

---

*This repository represents both a personal recipe collection and an open-source toolchain for building beautiful cookbooks from LaTeX source files.*

