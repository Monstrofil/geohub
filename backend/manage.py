#!/usr/bin/env python3
"""
Django-style management script for the Tagger application
"""
import sys
import os
import argparse
import importlib
from pathlib import Path


def get_available_commands():
    """Get all available commands from the cli.commands package"""
    commands = {}
    commands_dir = Path(__file__).parent / "cli" / "commands"
    
    if not commands_dir.exists():
        return commands
    
    for file_path in commands_dir.glob("*.py"):
        if file_path.name.startswith("__"):
            continue
        
        command_name = file_path.stem
        try:
            module = importlib.import_module(f"cli.commands.{command_name}")
            if hasattr(module, 'command'):
                commands[command_name] = module.command
        except ImportError as e:
            print(f"Warning: Could not import command '{command_name}': {e}")
    
    return commands


def main():
    """Main entry point for the management script"""
    parser = argparse.ArgumentParser(
        description="Tagger management utility",
        prog="manage.py"
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        metavar='<command>'
    )
    
    # Get available commands
    commands = get_available_commands()
    
    if not commands:
        print("No commands available. Make sure cli.commands package is properly set up.")
        sys.exit(1)
    
    # Add help for available commands
    if commands:  # Only if commands is a dict
        for command_name, command_class in commands.items():
            cmd_parser = subparsers.add_parser(
                command_name,
                help=command_class.help if hasattr(command_class, 'help') else f"Run {command_name} command"
            )
            # We'll let the command class handle its own argument parsing
    
    # Parse main arguments
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args, remaining = parser.parse_known_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Check if command exists
    if args.command not in commands:
        print(f"Unknown command: {args.command}")
        print(f"Available commands: {', '.join(commands.keys())}")
        sys.exit(1)
    
    # Execute the command
    command_class = commands[args.command]
    command_instance = command_class()
    
    try:
        command_instance.execute(remaining)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)


if __name__ == "__main__":
    # Add the backend directory to the Python path
    backend_dir = Path(__file__).parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    main()
