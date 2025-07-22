#!/usr/bin/env python3
"""
QA Testing Scenarios for Fides

Simple QA command-line tool for Fides testing scenarios.

Usage:
    python qa list
    python qa setup <scenario> [options]
    python qa teardown <scenario> [options]

Examples:
    python qa list
    python qa setup integration_with_many_datasets
    python qa teardown integration_with_many_datasets
"""

import sys
import argparse
import os
import importlib.util
import subprocess
from typing import Dict, Type
from pathlib import Path


def check_dependencies():
    """Check if requirements are installed and install them if needed."""
    try:
        import requests
    except ImportError:
        print("Installing QA testing dependencies...")
        qa_requirements = Path(__file__).parent / "requirements.txt"
        if qa_requirements.exists():
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(qa_requirements)], check=True)
        else:
            print("WARNING: Requirements file not found, attempting to install basic dependencies")
            subprocess.run([sys.executable, "-m", "pip", "install", "requests", "loguru"], check=True)


# Add qa directory to path for imports
qa_dir = os.path.dirname(os.path.abspath(__file__))
if qa_dir not in sys.path:
    sys.path.insert(0, qa_dir)

from utils import QATestScenario


def discover_scenarios() -> Dict[str, Type[QATestScenario]]:
    """Automatically discover scenario classes from files in the scenarios directory."""
    scenarios = {}
    qa_dir = os.path.dirname(os.path.abspath(__file__))
    scenarios_dir = os.path.join(qa_dir, 'scenarios')

    # Look for Python files in the scenarios directory
    if not os.path.exists(scenarios_dir):
        return scenarios

    for filename in os.listdir(scenarios_dir):
        if not filename.endswith('.py') or filename.startswith('_'):
            continue

        module_name = filename[:-3]  # Remove .py extension
        filepath = os.path.join(scenarios_dir, filename)

        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for classes that inherit from QATestScenario
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, QATestScenario) and
                        attr != QATestScenario):
                        scenarios[module_name] = attr
                        break  # Take the first scenario class found in the file

        except Exception:
            # Skip files that can't be imported or don't contain valid scenarios
            continue

    return scenarios


def get_scenario_description(scenario_class: Type[QATestScenario]) -> str:
    """Get description from a scenario class."""
    try:
        # Create a temporary instance to get the description property
        instance = scenario_class()
        return instance.description
    except Exception:
        # Fallback to class docstring if instantiation fails
        if scenario_class.__doc__:
            return scenario_class.__doc__.strip().split('\n')[0]
        return 'No description available'


def list_scenarios():
    """List all available scenarios."""
    try:
        from rich.console import Console
        from rich.table import Table

        use_rich = True
    except ImportError:
        use_rich = False

    scenarios = discover_scenarios()

    if use_rich:
        console = Console()

        if not scenarios:
            console.print("[red]❌ No scenarios found![/red]")
            console.print("\n[dim]To create a scenario:[/dim]")
            console.print(
                "  [cyan]1.[/cyan] Create a Python file (e.g., my_scenario.py)"
            )
            console.print(
                "  [cyan]2.[/cyan] Define a class inheriting from QATestScenario"
            )
            console.print("  [cyan]3.[/cyan] The filename becomes the scenario name")
            return

        console.print(f"[green]✅ Found {len(scenarios)} scenario(s)[/green]")

        table = Table(
            title="Available QA Scenarios",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Scenario", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Arguments", style="yellow")

        for name, scenario_class in scenarios.items():
            description = get_scenario_description(scenario_class)

            # Show available arguments
            args = scenario_class.arguments
            if args:
                arg_list = []
                for arg_name, arg_spec in args.items():
                    arg_type = arg_spec.type.__name__
                    arg_default = arg_spec.default
                    arg_list.append(
                        f"--{arg_name} ({arg_type}, default: {arg_default})"
                    )
                arguments = "\n".join(arg_list)
            else:
                arguments = "None"

            table.add_row(name, description, arguments)

        console.print(table)

        console.print("\n[dim]Usage:[/dim]")
        console.print("  [cyan]python qa <scenario> setup [OPTIONS][/cyan]")
        console.print("  [cyan]python qa <scenario> teardown [OPTIONS][/cyan]")
        console.print("\n[dim]Examples:[/dim]")
        console.print("  [green]python qa integration_with_many_datasets setup[/green]")
        console.print(
            "  [green]python qa integration_with_many_datasets setup --datasets 10[/green]"
        )
        console.print(
            "  [green]python qa integration_with_many_datasets teardown --datasets 10[/green]"
        )

    else:
        # Fallback to plain text if Rich is not available
        print("\nAvailable QA Scenarios:")
        print("-" * 50)

        if not scenarios:
            print("  No scenarios found")
            print("\nTo create a scenario:")
            print("  1. Create a Python file (e.g., my_scenario.py)")
            print("  2. Define a class inheriting from QATestScenario")
            print("  3. The filename becomes the scenario name")
            return

        for name, scenario_class in scenarios.items():
            description = get_scenario_description(scenario_class)
            print(f"  {name}")
            print(f"    {description}")

            # Show available arguments
            args = scenario_class.arguments
            if args:
                print(f"    Arguments:")
                for arg_name, arg_spec in args.items():
                    arg_type = arg_spec.type.__name__
                    arg_default = arg_spec.default
                    arg_description = arg_spec.description
                    print(
                        f"      --{arg_name} ({arg_type}, default: {arg_default}): {arg_description}"
                    )
            print()

        print("Usage:")
        print("  python qa <scenario> setup [options]")
        print("  python qa <scenario> teardown [options]")


def create_scenario_instance(scenario_class: Type[QATestScenario], **kwargs):
    """Create a scenario instance using the new interface."""
    base_url = kwargs.get('base_url', 'http://localhost:8080')

    # Remove base_url from kwargs since it's handled separately
    scenario_kwargs = {k: v for k, v in kwargs.items() if k != 'base_url'}

    return scenario_class(base_url=base_url, **scenario_kwargs)


def main():
    # Check and install dependencies first
    check_dependencies()

    if len(sys.argv) < 2:
        print("Usage: python qa <scenario> <command> [options]")
        print("       python qa list")
        print("Commands: setup, teardown")
        print("Run 'python qa list' to see available scenarios")
        sys.exit(1)

    first_arg = sys.argv[1]

    if first_arg == "list":
        list_scenarios()
        return

    # Format: python qa <scenario> <command> [options]
    if len(sys.argv) < 3:
        print("ERROR: Missing command after scenario name")
        print("Usage: python qa <scenario> <command> [options]")
        print("Commands: setup, teardown")
        sys.exit(1)

    scenario_name = sys.argv[1]
    command = sys.argv[2]

    if command not in ["setup", "teardown"]:
        print(f"ERROR: Unknown command '{command}'")
        print("Available commands: setup, teardown")
        sys.exit(1)

    # Get the scenario class to determine its arguments
    scenarios = discover_scenarios()
    if scenario_name not in scenarios:
        print(f"ERROR: Unknown scenario '{scenario_name}'")
        print("Run 'python qa list' to see available scenarios")
        sys.exit(1)

    scenario_class = scenarios[scenario_name]

    # Build argument parser dynamically based on scenario's declared arguments
    parser = argparse.ArgumentParser(
        prog=f"python qa {scenario_name} {command}", add_help=False
    )

    # Always add base-url since it's common to all scenarios
    parser.add_argument(
        "--base-url",
        default="http://localhost:8080",
        help="Fides API base URL (default: http://localhost:8080)",
    )

    # Add scenario-specific arguments
    scenario_args = scenario_class.arguments
    for arg_name, arg_spec in scenario_args.items():
        arg_type = arg_spec.type
        arg_default = arg_spec.default
        arg_help = arg_spec.description

        parser.add_argument(
            f"--{arg_name}", type=arg_type, default=arg_default, help=arg_help
        )

    parser.add_argument("--help", action="help", help="Show this help message")

    # Parse remaining args (skip 'qa', scenario, and command)
    try:
        args = parser.parse_args(sys.argv[3:])
    except SystemExit:
        sys.exit(1)

    # Build kwargs from parsed arguments
    kwargs = {"base_url": args.base_url}
    for arg_name in scenario_args.keys():
        kwargs[arg_name] = getattr(args, arg_name)

    # Create scenario instance and run the command
    try:
        scenario = create_scenario_instance(scenario_class, **kwargs)
    except Exception as e:
        print(f"ERROR: Failed to create scenario '{scenario_name}': {e}")
        sys.exit(1)

    if command == "setup":
        # Always teardown first for idempotent setup
        print("Running teardown first for idempotent setup...")
        teardown_success = scenario.teardown()
        if not teardown_success:
            print("Warning: Teardown had issues, but continuing with setup...")

        print("Running setup...")
        success = scenario.setup()
    else:  # teardown
        success = scenario.teardown()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
