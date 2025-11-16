#!/usr/bin/env python3
"""
Kodi Add-on Python Formatter
Scans a directory for Python files and formats them using black and isort.
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required formatting tools are installed."""
    dependencies = {"black": "black", "isort": "isort"}

    missing = []
    for name, command in dependencies.items():
        try:
            subprocess.run([command, "--version"], capture_output=True, check=True)
            logger.info(f"✓ {name} is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(name)
            logger.error(f"✗ {name} is not installed")

    if missing:
        logger.error("\nMissing dependencies! Install them using:")
        logger.error(f"pip install {' '.join(missing)}")
        return False

    return True


def format_python_file(file_path, dry_run=False):
    """Format a single Python file using black and isort."""
    try:
        # First, organize imports with isort
        isort_cmd = ["isort", str(file_path)]
        if dry_run:
            isort_cmd.append("--diff")

        result = subprocess.run(isort_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"isort warning for {file_path}: {result.stderr}")

        # Then format with black
        black_cmd = ["black", str(file_path)]
        if dry_run:
            black_cmd.extend(["--diff", "--check"])
        else:
            black_cmd.append("--quiet")

        result = subprocess.run(black_cmd, capture_output=True, text=True)

        if dry_run:
            if result.stdout:
                logger.info(f"Would format: {file_path}")
                return True
            else:
                logger.info(f"Already formatted: {file_path}")
                return False
        else:
            if result.returncode == 0:
                logger.info(f"✓ Formatted: {file_path}")
                return True
            else:
                logger.error(f"✗ Error formatting {file_path}: {result.stderr}")
                return False

    except Exception as e:
        logger.error(f"✗ Error processing {file_path}: {str(e)}")
        return False


def find_python_files(directory):
    """Find all Python files in the given directory."""
    path = Path(directory)
    if not path.exists():
        logger.error(f"Directory does not exist: {directory}")
        return []

    if not path.is_dir():
        logger.error(f"Path is not a directory: {directory}")
        return []

    python_files = list(path.rglob("*.py"))
    logger.info(f"Found {len(python_files)} Python files in {directory}")
    return python_files


def create_backup(file_path):
    """Create a backup of the file before formatting."""
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    try:
        backup_path.write_bytes(file_path.read_bytes())
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup for {file_path}: {str(e)}")
        return None


def format_directory(directory, dry_run=False, backup=False, exclude_patterns=None):
    """Format all Python files in the given directory."""
    python_files = find_python_files(directory)

    if not python_files:
        logger.info("No Python files found to format.")
        return

    # Filter out excluded patterns
    if exclude_patterns:
        filtered_files = []
        for file_path in python_files:
            excluded = False
            for pattern in exclude_patterns:
                if pattern in str(file_path):
                    logger.info(f"Excluding: {file_path} (matches pattern: {pattern})")
                    excluded = True
                    break
            if not excluded:
                filtered_files.append(file_path)
        python_files = filtered_files

    logger.info(
        f"\n{'Would format' if dry_run else 'Formatting'} {len(python_files)} files..."
    )

    formatted_count = 0
    error_count = 0

    for file_path in python_files:
        # Create backup if requested
        if backup and not dry_run:
            backup_path = create_backup(file_path)
            if backup_path:
                logger.debug(f"Created backup: {backup_path}")

        # Format the file
        if format_python_file(file_path, dry_run):
            formatted_count += 1
        else:
            error_count += 1

    # Summary
    logger.info(f"\n{'Dry run' if dry_run else 'Formatting'} complete!")
    logger.info(
        f"Files {'that would be' if dry_run else ''} formatted: {formatted_count}"
    )
    if error_count > 0:
        logger.warning(f"Files with errors: {error_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Format Python files in Kodi add-on directories"
    )
    parser.add_argument("directory", help="Path to the Kodi add-on directory to scan")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be formatted without making changes",
    )
    parser.add_argument(
        "--backup", action="store_true", help="Create .bak files before formatting"
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Patterns to exclude from formatting (e.g., 'test_' 'old/')",
    )

    args = parser.parse_args()

    # Check if dependencies are installed
    if not check_dependencies():
        sys.exit(1)

    # Format the directory
    format_directory(
        args.directory,
        dry_run=args.dry_run,
        backup=args.backup,
        exclude_patterns=args.exclude,
    )


if __name__ == "__main__":
    main()
