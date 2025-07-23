#!/usr/bin/env python3
"""
Rich formatting utilities for QA scenarios.

Provides reusable components for CLI output including:
- Phase headers (Setup/Cleanup/etc.)
- Step formatting with numbering
- Progress bars for resource operations
- Status messages and summaries
- Error and success formatting
"""
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TextColumn, BarColumn, MofNCompleteColumn, TimeElapsedColumn

import time
from typing import Dict, List, Any, Optional, Callable
from contextlib import contextmanager


class RichFormatter:
    """Rich formatting utilities for QA scenarios."""

    def __init__(self):
        try:
            self.Panel = Panel
            self.Progress = Progress
            self.TextColumn = TextColumn
            self.BarColumn = BarColumn
            self.MofNCompleteColumn = MofNCompleteColumn
            self.TimeElapsedColumn = TimeElapsedColumn
            self.rich_available = True
            self.console = Console()
        except ImportError:
            self.rich_available = False
            self.console = None

    def phase_header(self, title: str, style: str = "cyan") -> None:
        """Print a beautiful phase header (e.g., 'Setup Phase', 'Cleanup Phase')."""
        if self.rich_available and self.console:
            self.console.print()
            self.console.print(self.Panel.fit(title, style=style))
        else:
            print(f"\n=== {title} ===")

    def step_header(self, step_num: int, title: str) -> None:
        """Print a numbered step header."""
        if self.rich_available and self.console:
            self.console.print(f"\n[bold cyan]Step {step_num}: {title}...[/bold cyan]")
        else:
            print(f"\nStep {step_num}: {title}...")

    def success(self, message: str, indent: int = 2) -> None:
        """Print a success message with checkmark."""
        indent_str = " " * indent
        if self.rich_available and self.console:
            self.console.print(f"{indent_str}[green]✓[/green] {message}")
        else:
            print(f"{indent_str}✓ {message}")

    def error(self, message: str, indent: int = 2) -> None:
        """Print an error message with X mark."""
        indent_str = " " * indent
        if self.rich_available and self.console:
            self.console.print(f"{indent_str}[red]❌[/red] {message}")
        else:
            print(f"{indent_str}❌ {message}")

    def warning(self, message: str, indent: int = 2) -> None:
        """Print a warning message."""
        indent_str = " " * indent
        if self.rich_available and self.console:
            self.console.print(f"{indent_str}[yellow]⚠️[/yellow] {message}")
        else:
            print(f"{indent_str}⚠️ {message}")

    def info(self, message: str, indent: int = 2) -> None:
        """Print an info message."""
        indent_str = " " * indent
        if self.rich_available and self.console:
            self.console.print(f"{indent_str}[blue]ℹ[/blue] {message}")
        else:
            print(f"{indent_str}• {message}")

    def already_cleaned(self, resource_type: str, resource_id: str, indent: int = 2) -> None:
        """Print a message for resources that are already cleaned/don't exist."""
        indent_str = " " * indent
        if self.rich_available and self.console:
            self.console.print(f"{indent_str}[dim]•[/dim] {resource_type} {resource_id} (already cleaned)")
        else:
            print(f"{indent_str}• {resource_type} {resource_id} (already cleaned)")

    @contextmanager
    def progress_bar(self, description: str, total: int, **fields):
        """Context manager for a progress bar with custom fields."""
        if not self.rich_available:
            print(f"{description} (0/{total})")
            yield _FallbackProgress(description, total)
            return

        # Build columns dynamically based on provided fields
        columns = [
            self.TextColumn("[progress.description]{task.description}"),
            self.BarColumn(),
            self.MofNCompleteColumn(),
        ]

        # Add custom field columns
        for field_name in fields.keys():
            columns.append(self.TextColumn(f"• [green]{field_name.title()}: {{task.fields[{field_name}]}}[/green]"))

        columns.append(self.TimeElapsedColumn())

        with self.Progress(*columns, refresh_per_second=10) as progress:
            task = progress.add_task(f"  {description}", total=total, **fields)
            yield _RichProgressTask(progress, task)

    def summary_table(self, title: str, data: Dict[str, int]) -> None:
        """Print a summary table of operations."""
        if self.rich_available and self.console:
            self.console.print()
            self.console.print(f"[bold green]{title}:[/bold green]")
            total = sum(data.values())
            for resource_type, count in data.items():
                self.console.print(f"  [cyan]{resource_type.capitalize()}:[/cyan] {count}")
            self.console.print(f"  [bold]Total:[/bold] {total}")
            self.console.print()
        else:
            print(f"\n{title}:")
            total = sum(data.values())
            for resource_type, count in data.items():
                print(f"  {resource_type.capitalize()}: {count}")
            print(f"  Total: {total}\n")

    def final_success(self, message: str) -> None:
        """Print a final success message."""
        if self.rich_available and self.console:
            self.console.print()
            self.console.print(f"[bold green]✓ {message}[/bold green]")
            self.console.print()
        else:
            print(f"\n✓ {message}\n")

    def final_error(self, message: str) -> None:
        """Print a final error message."""
        if self.rich_available and self.console:
            self.console.print(f"\n[red]❌ {message}[/red]")
        else:
            print(f"\n❌ {message}")


class _RichProgressTask:
    """Wrapper for Rich progress task."""

    def __init__(self, progress, task_id):
        self.progress = progress
        self.task_id = task_id

    def advance(self, amount: int = 1):
        """Advance the progress bar."""
        self.progress.advance(self.task_id, amount)

    def update(self, **fields):
        """Update progress bar fields."""
        self.progress.update(self.task_id, **fields)


class _FallbackProgress:
    """Fallback progress tracker when Rich is not available."""

    def __init__(self, description: str, total: int):
        self.description = description
        self.total = total
        self.current = 0
        self.last_percent = -1

    def advance(self, amount: int = 1):
        """Advance the fallback progress."""
        self.current += amount
        percent = int((self.current / self.total) * 100)
        if percent != self.last_percent and percent % 20 == 0:  # Show every 20%
            print(f"  {self.description} ({self.current}/{self.total}) - {percent}%")
            self.last_percent = percent

    def update(self, **fields):
        """Update fallback progress (no-op since we can't show fields in plain text)."""
        pass


# Convenience functions for common operations
def create_resources_with_progress(
    formatter: RichFormatter,
    resource_type: str,
    items: List[Any],
    create_func: Callable,
    get_key_func: Optional[Callable] = None,
    sleep_time: float = 0.05
) -> Dict[str, List[str]]:
    """
    Generic function to create resources with a progress bar.

    Args:
        formatter: RichFormatter instance
        resource_type: Name of resource type (e.g., "datasets", "systems")
        items: List of items to create
        create_func: Function to call for each item (should take item as argument)
        get_key_func: Function to extract key from item (defaults to str(item))
        sleep_time: Time to sleep between operations

    Returns:
        Dict with 'created' and 'failed' lists
    """
    if get_key_func is None:
        get_key_func = str

    created = []
    failed = []

    with formatter.progress_bar(
        f"Creating {len(items)} {resource_type}...",
        total=len(items),
        created=0,
        failed=0
    ) as progress:

        for item in items:
            try:
                create_func(item)
                created.append(get_key_func(item))
                progress.update(created=len(created))
                time.sleep(sleep_time)
            except Exception as e:
                key = get_key_func(item)
                formatter.error(f"Failed to create {resource_type[:-1]} {key}: {e}")
                failed.append(key)
                progress.update(failed=len(failed))
                continue

            progress.advance()

    formatter.success(f"{resource_type.capitalize()} creation completed: {len(created)}/{len(items)} successful")
    return {'created': created, 'failed': failed}


def delete_resources_with_progress(
    formatter: RichFormatter,
    resource_type: str,
    keys: List[str],
    delete_func: Callable,
    sleep_time: float = 0.05
) -> int:
    """
    Generic function to delete resources with a progress bar.

    Args:
        formatter: RichFormatter instance
        resource_type: Name of resource type (e.g., "datasets", "systems")
        keys: List of resource keys to delete
        delete_func: Function to call for each key (should take key as argument and return bool)
        sleep_time: Time to sleep between operations

    Returns:
        Number of successfully deleted resources
    """
    deleted_count = 0

    if not keys:
        return deleted_count

    with formatter.progress_bar(
        f"Deleting {len(keys)} {resource_type}...",
        total=len(keys),
        deleted=0
    ) as progress:

        for key in keys:
            if delete_func(key):
                deleted_count += 1
                progress.update(deleted=deleted_count)

            progress.advance()
            time.sleep(sleep_time)

    return deleted_count
