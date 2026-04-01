"""
Utility functions for ACRCloud CLI
"""

import click
import json
from typing import List, Any


def output_json(data: dict, pretty: bool = True):
    """Output data as formatted JSON"""
    if pretty:
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        click.echo(json.dumps(data, ensure_ascii=False))


def output_table(headers: List[str], rows: List[List[Any]]):
    """Output data as a formatted table"""
    if not rows:
        click.echo("No data to display")
        return
    
    # Calculate column widths
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(str(header))
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(str(row[i])))
        col_widths.append(max_width + 2)  # Add padding
    
    # Print header
    header_line = ""
    for i, header in enumerate(headers):
        header_line += str(header).ljust(col_widths[i])
    click.echo(header_line)
    click.echo("-" * sum(col_widths))
    
    # Print rows
    for row in rows:
        row_line = ""
        for i, cell in enumerate(row):
            if i < len(col_widths):
                row_line += str(cell).ljust(col_widths[i])
        click.echo(row_line)


def confirm_action(message: str) -> bool:
    """Ask user for confirmation"""
    return click.confirm(message, default=False)


def format_bytes(size_bytes: int) -> str:
    """Format bytes to human-readable string"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"


def parse_metadata_template(template_str: str) -> dict:
    """Parse metadata template string to dict"""
    try:
        return json.loads(template_str)
    except json.JSONDecodeError as e:
        raise click.BadParameter(f"Invalid JSON: {e}")


def validate_region(ctx, param, value):
    """Validate region parameter"""
    valid_regions = ['eu-west-1', 'us-west-2', 'ap-southeast-1']
    if value and value not in valid_regions:
        raise click.BadParameter(f"Invalid region. Must be one of: {', '.join(valid_regions)}")
    return value


def validate_bucket_type(ctx, param, value):
    """Validate bucket type parameter"""
    valid_types = ['File', 'Live', 'LiveRec', 'LiveTimeshift']
    if value and value not in valid_types:
        raise click.BadParameter(f"Invalid bucket type. Must be one of: {', '.join(valid_types)}")
    return value
