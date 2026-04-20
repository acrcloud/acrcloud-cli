#!/usr/bin/env python3
"""
ACRCloud CLI - Main entry point
"""

import click
import os
import sys
from .commands import buckets, projects, config_cmd, filescan, bm_cs_projects, bm_db_projects, ucf_projects, billing
from .config import Config
from . import __version__


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="acrcloud")
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
@click.option('--access-token', '-t', envvar='ACRCLOUD_ACCESS_TOKEN', help='ACRCloud Access Token')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, config, access_token, verbose):
    """
    ACRCloud CLI - Manage your ACRCloud resources from the command line.
    
    Examples:
        acrcloud buckets list
        acrcloud base-projects create --name my-project --type AVR
        acrcloud buckets files upload --bucket-id 12345 --file audio.mp3
    
    For more information, visit: https://docs.acrcloud.com/reference/console-api
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    # Load configuration
    cfg = Config(config_path=config)
    ctx.obj['config'] = cfg
    
    # Use command-line token if provided, otherwise use config file
    token = access_token or cfg.get('access_token')
    ctx.obj['access_token'] = token
    ctx.obj['base_url'] = cfg.get('base_url', 'https://api-v2.acrcloud.com/api')
    
    # If no subcommand invoked, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Register commands
cli.add_command(config_cmd.config)
cli.add_command(buckets.buckets)
cli.add_command(projects.projects)
cli.add_command(filescan.filescan)
cli.add_command(bm_cs_projects.bm_cs_projects)
cli.add_command(bm_db_projects.bm_db_projects)
cli.add_command(ucf_projects.ucf_projects)
cli.add_command(billing.billing)


def main():
    """Main entry point"""
    # Check if running a command that requires auth
    args = sys.argv[1:]
    
    # Commands that don't require authentication
    no_auth_commands = ['config']
    
    # Check if first argument is a no-auth command
    requires_auth = True
    if args and args[0] in no_auth_commands:
        requires_auth = False
    
    # If auth is required, check for token
    if requires_auth:
        # Check for token in args
        has_token = False
        for i, arg in enumerate(args):
            if arg in ['-t', '--access-token'] and i + 1 < len(args):
                has_token = True
                break
            if arg.startswith('--access-token=') or arg.startswith('-t='):
                has_token = True
                break
        
        # Check environment variable
        if not has_token and os.environ.get('ACRCLOUD_ACCESS_TOKEN'):
            has_token = True
        
        # Check config file
        if not has_token:
            cfg = Config()
            if cfg.get('access_token'):
                has_token = True
        
        if not has_token:
            click.echo("Error: Access token is required. Set it via:", err=True)
            click.echo("  1. --access-token option", err=True)
            click.echo("  2. ACRCLOUD_ACCESS_TOKEN environment variable", err=True)
            click.echo("  3. Config file (run: acrcloud config set access_token YOUR_TOKEN)", err=True)
            sys.exit(1)
    
    cli()


if __name__ == '__main__':
    main()
