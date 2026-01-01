#!/usr/bin/env python3

"""Compile all individual recipe .tex files to PDFs in place

This script finds all .tex recipe files and compiles them using xelatex,
outputting PDFs in the same directory as the source files.

Only compiles files where the .tex source is newer than the existing PDF,
unless --force is used. Always cleans up auxiliary files after successful
compilation.

Usage:
    python _tools/compile_recipes.py [--force]
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple
from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
    SpinnerColumn
)

def find_recipe_files(root_dir: Path) -> List[Path]:
    """Find all .tex recipe files, excluding templates
    
    Args:
        root_dir: Root directory to search from
        
    Returns:
        List of Path objects for recipe .tex files
    """
    recipe_files = []
    exclude_dirs = {'_build', '_templates', '_tools', '.git'}
    
    for tex_file in root_dir.rglob('*.tex'):
        # Skip files in excluded directories
        if any(excluded in tex_file.parts for excluded in exclude_dirs):
            continue
        recipe_files.append(tex_file)
    
    return sorted(recipe_files)

def needs_compilation(tex_path: Path) -> bool:
    """Check if .tex file needs compilation (newer than PDF or PDF missing)
    
    Args:
        tex_path: Path to .tex file
        
    Returns:
        True if compilation is needed, False if PDF is up to date
    """
    pdf_path = tex_path.with_suffix('.pdf')
    
    # Always compile if PDF doesn't exist
    if not pdf_path.exists():
        return True
    
    # Compile if .tex is newer than PDF
    tex_mtime = tex_path.stat().st_mtime
    pdf_mtime = pdf_path.stat().st_mtime
    
    return tex_mtime > pdf_mtime

def compile_tex_file(tex_path: Path) -> Tuple[bool, str]:
    """Compile a single .tex file using xelatex
    
    Args:
        tex_path: Path to .tex file
        
    Returns:
        Tuple of (success: bool, error_message: str)
    """
    work_dir = tex_path.parent
    
    try:
        # Run xelatex twice for proper cross-references/TOC
        for run in range(2):
            result = subprocess.run(
                [
                    'xelatex',
                    '-interaction=nonstopmode',
                    f'-jobname={tex_path.stem}',
                    str(tex_path.name)
                ],
                cwd=work_dir,
                capture_output=True,
                text=True
            )
            
            # Check for fatal errors
            if "Fatal error occurred" in result.stdout or "Emergency stop" in result.stdout:
                return False, result.stdout[-1000:]  # Last 1000 chars of output
        
        # Always clean up auxiliary files after successful compilation
        aux_extensions = ['.aux', '.log', '.toc', '.out', '.synctex.gz']
        for ext in aux_extensions:
            aux_file = work_dir / f"{tex_path.stem}{ext}"
            if aux_file.exists():
                aux_file.unlink()
        
        return True, ""
        
    except subprocess.SubprocessError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Compile all recipe .tex files to PDFs in place"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force recompilation of all files, even if PDF is up to date'
    )
    parser.add_argument(
        '--root',
        type=Path,
        default=Path(__file__).parent.parent,
        help='Root directory to search for .tex files (default: project root)'
    )
    args = parser.parse_args()
    
    console = Console()
    
    # Find all recipe files
    console.print("[bold cyan]Finding recipe files...[/bold cyan]")
    recipe_files = find_recipe_files(args.root)
    
    if not recipe_files:
        console.print("[yellow]No recipe files found[/yellow]")
        return 0
    
    console.print(f"[green]Found {len(recipe_files)} recipe files[/green]\n")
    
    # Compile each file
    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("[dim]│[/dim]"),
        TextColumn("[dim]Elapsed:[/dim]"),
        TimeElapsedColumn(),
        TextColumn("[dim]│ ETA:[/dim]"),
        TimeRemainingColumn(),
        console=console,
        expand=True
    ) as progress:
        task = progress.add_task(
            "[cyan]Processing recipes...",
            total=len(recipe_files)
        )
        
        for tex_file in recipe_files:
            # Check if we should skip (unless --force is used)
            if not args.force and not needs_compilation(tex_file):
                progress.update(
                    task,
                    description=f"[dim]Skipping[/dim] [cyan]{tex_file.name}[/cyan] [dim](up to date)[/dim]"
                )
                results.append((tex_file, True, "", True))  # (file, success, error, skipped)
            else:
                progress.update(
                    task,
                    description=f"[yellow]Compiling[/yellow] [cyan]{tex_file.name}[/cyan]"
                )
                success, error = compile_tex_file(tex_file)
                results.append((tex_file, success, error, False))  # (file, success, error, skipped)
            
            progress.advance(task)
    
    # Print summary
    console.print("\n[bold]Compilation Summary[/bold]")
    
    successful = [r for r in results if r[1] and not r[3]]  # Compiled successfully
    skipped = [r for r in results if r[3]]  # Skipped (up to date)
    failed = [r for r in results if not r[1] and not r[3]]  # Failed compilation
    
    console.print(f"✓ Compiled: [green]{len(successful)}[/green]")
    console.print(f"⊘ Skipped (up to date): [dim]{len(skipped)}[/dim]")
    console.print(f"✗ Failed: [red]{len(failed)}[/red]\n")
    
    # Show failed files if any
    if failed:
        table = Table(title="Failed Compilations")
        table.add_column("File", style="cyan")
        table.add_column("Error", style="red", no_wrap=False)
        
        for tex_file, _, error, _ in failed:
            # Truncate long errors
            error_msg = error[-500:] if len(error) > 500 else error
            table.add_row(str(tex_file.relative_to(args.root)), error_msg)
        
        console.print(table)
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

