#!/usr/bin/env python3
"""
Kodi Add-on XML Formatter
Scans a directory for XML files and formats them with proper indentation and structure.
"""

import argparse
import logging
import os
import re
import sys
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def pretty_print_xml(element, encoding="UTF-8", indent="    ", preserve_cdata=True):
    """
    Pretty print an XML element with proper formatting.

    Args:
        element: XML Element or string to format
        encoding: Character encoding for the output
        indent: String to use for indentation
        preserve_cdata: Whether to preserve CDATA sections
    """
    # Convert element to string if needed
    if isinstance(element, ET.Element):
        rough_string = ET.tostring(element, encoding="unicode")
    else:
        rough_string = element

    # Preserve CDATA sections if requested
    cdata_sections = []
    if preserve_cdata:
        # Find and temporarily replace CDATA sections
        cdata_pattern = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.DOTALL)
        matches = list(cdata_pattern.finditer(rough_string))
        for i, match in enumerate(matches):
            placeholder = f"__CDATA_PLACEHOLDER_{i}__"
            cdata_sections.append((placeholder, match.group(0)))
            rough_string = rough_string.replace(match.group(0), placeholder)

    # Parse and pretty print
    try:
        dom = minidom.parseString(rough_string)
        pretty_xml = dom.toprettyxml(indent=indent, encoding=encoding)

        # Decode if we got bytes
        if isinstance(pretty_xml, bytes):
            pretty_xml = pretty_xml.decode(encoding)

        # Remove extra blank lines
        lines = pretty_xml.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]
        pretty_xml = "\n".join(non_empty_lines)

        # Restore CDATA sections
        for placeholder, original in cdata_sections:
            pretty_xml = pretty_xml.replace(placeholder, original)

        # Ensure single newline at end
        pretty_xml = pretty_xml.rstrip() + "\n"

        return pretty_xml

    except Exception as e:
        logger.error(f"Error in pretty printing: {str(e)}")
        return None


def format_xml_file(
    file_path: Path,
    dry_run: bool = False,
    indent: str = "    ",
    encoding: str = "UTF-8",
    preserve_comments: bool = True,
) -> bool:
    """
    Format a single XML file.

    Args:
        file_path: Path to the XML file
        dry_run: If True, show what would be done without making changes
        indent: String to use for indentation
        encoding: Character encoding
        preserve_comments: Whether to preserve XML comments

    Returns:
        True if file was formatted (or would be), False otherwise
    """
    try:
        # Read the original content
        with open(file_path, "r", encoding=encoding) as f:
            original_content = f.read()

        # Skip empty files
        if not original_content.strip():
            logger.info(f"Skipping empty file: {file_path}")
            return False

        # Check if it's valid XML
        try:
            # Parse to check validity
            ET.fromstring(original_content)
        except ET.ParseError as e:
            logger.error(f"✗ Invalid XML in {file_path}: {str(e)}")
            return False

        # Format the content
        formatted_content = pretty_print_xml(
            original_content, encoding=encoding, indent=indent, preserve_cdata=True
        )

        if formatted_content is None:
            logger.error(f"✗ Could not format {file_path}")
            return False

        # Check if content changed
        if formatted_content.strip() == original_content.strip():
            logger.info(f"Already formatted: {file_path}")
            return False

        if dry_run:
            logger.info(f"Would format: {file_path}")
            # Optionally show a diff
            logger.debug(f"Original lines: {len(original_content.splitlines())}")
            logger.debug(f"Formatted lines: {len(formatted_content.splitlines())}")
            return True
        else:
            # Write the formatted content
            with open(file_path, "w", encoding=encoding) as f:
                f.write(formatted_content)
            logger.info(f"✓ Formatted: {file_path}")
            return True

    except Exception as e:
        logger.error(f"✗ Error processing {file_path}: {str(e)}")
        return False


def find_xml_files(
    directory: str, exclude_patterns: Optional[List[str]] = None
) -> List[Path]:
    """Find all XML files in the given directory."""
    path = Path(directory)
    if not path.exists():
        logger.error(f"Directory does not exist: {directory}")
        return []

    if not path.is_dir():
        logger.error(f"Path is not a directory: {directory}")
        return []

    xml_files = []
    for file_path in path.rglob("*.xml"):
        # Skip if matches exclude pattern
        if exclude_patterns:
            excluded = False
            for pattern in exclude_patterns:
                if pattern in str(file_path):
                    logger.info(f"Excluding: {file_path} (matches pattern: {pattern})")
                    excluded = True
                    break
            if excluded:
                continue

        xml_files.append(file_path)

    logger.info(f"Found {len(xml_files)} XML files in {directory}")
    return xml_files


def create_backup(file_path: Path) -> Optional[Path]:
    """Create a backup of the file before formatting."""
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    try:
        backup_path.write_bytes(file_path.read_bytes())
        logger.debug(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup for {file_path}: {str(e)}")
        return None


def validate_xml_structure(file_path: Path) -> bool:
    """
    Validate XML structure and check for common Kodi XML issues.

    Args:
        file_path: Path to the XML file

    Returns:
        True if valid, False otherwise
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse the XML
        root = ET.fromstring(content)

        # Check for common Kodi addon.xml requirements
        if file_path.name == "addon.xml":
            if root.tag != "addon":
                logger.warning(
                    f"addon.xml should have 'addon' as root element in {file_path}"
                )

            # Check required attributes
            required_attrs = ["id", "name", "version", "provider-name"]
            missing_attrs = [attr for attr in required_attrs if attr not in root.attrib]
            if missing_attrs:
                logger.warning(
                    f"Missing required attributes in {file_path}: {missing_attrs}"
                )

        return True

    except Exception as e:
        logger.error(f"Validation error in {file_path}: {str(e)}")
        return False


def format_directory(
    directory: str,
    dry_run: bool = False,
    backup: bool = False,
    exclude_patterns: Optional[List[str]] = None,
    indent: str = "    ",
    encoding: str = "UTF-8",
    validate: bool = True,
):
    """Format all XML files in the given directory."""
    xml_files = find_xml_files(directory, exclude_patterns)

    if not xml_files:
        logger.info("No XML files found to format.")
        return

    logger.info(
        f"\n{'Would format' if dry_run else 'Formatting'} {len(xml_files)} files..."
    )

    formatted_count = 0
    error_count = 0
    validation_errors = 0

    for file_path in xml_files:
        # Validate first if requested
        if validate:
            if not validate_xml_structure(file_path):
                validation_errors += 1
                if not dry_run:
                    logger.warning(f"Skipping {file_path} due to validation errors")
                    continue

        # Create backup if requested
        if backup and not dry_run:
            if not create_backup(file_path):
                logger.warning(f"Skipping {file_path} - backup creation failed")
                continue

        # Format the file
        if format_xml_file(file_path, dry_run, indent, encoding):
            formatted_count += 1
        else:
            error_count += 1

    # Summary
    logger.info(f"\n{'Dry run' if dry_run else 'Formatting'} complete!")
    logger.info(
        f"Files {'that would be' if dry_run else ''} formatted: {formatted_count}"
    )
    if validation_errors > 0:
        logger.warning(f"Files with validation errors: {validation_errors}")
    if error_count > 0:
        logger.warning(f"Files with formatting errors: {error_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Format XML files in Kodi add-on directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Format all XML files in an addon directory
  python format_xml.py /path/to/addon

  # Preview changes without modifying files
  python format_xml.py /path/to/addon --dry-run

  # Create backups and use 2-space indentation
  python format_xml.py /path/to/addon --backup --indent "  "

  # Exclude certain patterns
  python format_xml.py /path/to/addon --exclude .git/ temp/ test.xml
""",
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
        help="Patterns to exclude from formatting (e.g., '.git/' 'temp/')",
    )
    parser.add_argument(
        "--indent",
        default="    ",
        help="String to use for indentation (default: 4 spaces)",
    )
    parser.add_argument(
        "--encoding",
        default="UTF-8",
        help="Character encoding for XML files (default: UTF-8)",
    )
    parser.add_argument(
        "--no-validate", action="store_true", help="Skip XML validation checks"
    )

    args = parser.parse_args()

    # Format the directory
    format_directory(
        args.directory,
        dry_run=args.dry_run,
        backup=args.backup,
        exclude_patterns=args.exclude,
        indent=args.indent,
        encoding=args.encoding,
        validate=not args.no_validate,
    )


if __name__ == "__main__":
    main()
