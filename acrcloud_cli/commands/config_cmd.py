"""
Config command for ACRCloud CLI
"""

import click
from ..config import Config


@click.group(name='config')
def config():
    """Manage ACRCloud CLI configuration"""
    pass


@config.command(name='set')
@click.argument('key')
@click.argument('value')
@click.option('--config-path', '-c', type=click.Path(), 
              help='Path to config file')
def set_config(key, value, config_path):
    """Set a configuration value
    
    Examples:
        acrcloud config set access_token YOUR_ACCESS_TOKEN
        acrcloud config set base_url https://api-v2.acrcloud.com/api
    """
    cfg = Config(config_path=config_path)
    cfg.set(key, value)
    click.echo(f"✓ Set {key} = {value}")


@config.command(name='get')
@click.argument('key')
@click.option('--config-path', '-c', type=click.Path(),
              help='Path to config file')
def get_config(key, config_path):
    """Get a configuration value
    
    Examples:
        acrcloud config get access_token
    """
    cfg = Config(config_path=config_path)
    value = cfg.get(key)
    if value:
        click.echo(value)
    else:
        click.echo(f"Key '{key}' not found")


@config.command(name='list')
@click.option('--config-path', '-c', type=click.Path(),
              help='Path to config file')
def list_config(config_path):
    """List all configuration values"""
    cfg = Config(config_path=config_path)
    config_data = cfg.list()
    
    if not config_data:
        click.echo("No configuration found")
        return
    
    click.echo("Configuration:")
    click.echo("-" * 40)
    for key, value in config_data.items():
        # Mask sensitive values
        if key in ['access_token', 'secret'] and value:
            display_value = value[:10] + "..." if len(value) > 10 else value
        else:
            display_value = value
        click.echo(f"  {key}: {display_value}")


@config.command(name='delete')
@click.argument('key')
@click.option('--config-path', '-c', type=click.Path(),
              help='Path to config file')
def delete_config(key, config_path):
    """Delete a configuration value
    
    Examples:
        acrcloud config delete access_token
    """
    cfg = Config(config_path=config_path)
    cfg.delete(key)
    click.echo(f"✓ Deleted {key}")
