"""
Channels command for ACRCloud CLI
"""

import click
import json
from ..api import ACRCloudAPI
from ..utils import output_json, output_table, confirm_action


@click.group(name='channels')
@click.pass_context
def channels(ctx):
    """Manage live channels in buckets"""
    ctx.obj['api'] = ACRCloudAPI(
        ctx.obj['access_token'],
        ctx.obj['base_url']
    )


@channels.command(name='list')
@click.option('--bucket-id', '-b', required=True, type=int, help='Bucket ID')
@click.option('--page', '-p', default=1, help='Page number')
@click.option('--per-page', '-n', default=20, help='Results per page')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list_channels(ctx, bucket_id, page, per_page, output):
    """List live channels in a bucket
    
    Examples:
        acrcloud buckets channels list --bucket-id 12345
    """
    api = ctx.obj['api']
    
    try:
        result = api.list_channels(bucket_id=bucket_id, page=page, per_page=per_page)
        
        if output == 'json':
            output_json(result)
        else:
            channels_data = result.get('data', [])
            if not channels_data:
                click.echo("No channels found")
                return
            
            headers = ['ID', 'Name', 'URL', 'Record', 'Timeshift']
            rows = []
            for channel in channels_data:
                rows.append([
                    channel.get('id'),
                    channel.get('name', '-')[:25],
                    channel.get('url', '-')[:40],
                    'Yes' if channel.get('record') else 'No',
                    f"{channel.get('timeshift', 0)}h" if channel.get('timeshift') else '-'
                ])
            output_table(headers, rows)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@channels.command(name='get')
@click.argument('channel_id', type=int)
@click.option('--bucket-id', '-b', required=True, type=int, help='Bucket ID')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def get_channel(ctx, channel_id, bucket_id, output):
    """Get channel details
    
    Examples:
        acrcloud buckets channels get 67890 --bucket-id 12345
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_channel(bucket_id=bucket_id, channel_id=channel_id)
        
        if output == 'json':
            output_json(result)
        else:
            channel = result.get('data', {})
            if not channel:
                click.echo("Channel not found")
                return
            
            click.echo(f"Channel Details (ID: {channel_id}):")
            click.echo("-" * 40)
            click.echo(f"  Name: {channel.get('name')}")
            click.echo(f"  URL: {channel.get('url')}")
            click.echo(f"  Record: {'Yes' if channel.get('record') else 'No'}")
            click.echo(f"  Timeshift: {channel.get('timeshift', 0)} hours")
            click.echo(f"  User Defined: {json.dumps(channel.get('user_defined', {}))}")
            click.echo(f"  Created: {channel.get('created_at')}")
            click.echo(f"  Updated: {channel.get('updated_at')}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@channels.command(name='create')
@click.option('--bucket-id', '-b', required=True, type=int, help='Bucket ID')
@click.option('--name', '-n', required=True, help='Channel name')
@click.option('--url', '-u', required=True, help='Stream URL')
@click.option('--record', '-r', type=int, help='Record duration in hours')
@click.option('--timeshift', '-t', type=int, help='Timeshift duration in hours')
@click.option('--user-defined', '-d', help='User-defined metadata (JSON string)')
@click.pass_context
def create_channel(ctx, bucket_id, name, url, record, timeshift, user_defined):
    """Create a live channel
    
    Examples:
        acrcloud buckets channels create --bucket-id 12345 --name "Radio One" --url "http://stream.example.com/radio"
        acrcloud buckets channels create -b 12345 -n "TV Channel" -u "http://tv.example.com/stream" -r 24 -t 72
    """
    api = ctx.obj['api']
    
    user_defined_dict = json.loads(user_defined) if user_defined else None
    
    try:
        result = api.create_channel(
            bucket_id=bucket_id,
            name=name,
            url=url,
            record=record,
            timeshift=timeshift,
            user_defined=user_defined_dict
        )
        
        channel = result.get('data', {})
        click.echo(f"✓ Channel created successfully!")
        click.echo(f"  ID: {channel.get('id')}")
        click.echo(f"  Name: {channel.get('name')}")
        click.echo(f"  URL: {channel.get('url')}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@channels.command(name='update')
@click.argument('channel_id', type=int)
@click.option('--bucket-id', '-b', required=True, type=int, help='Bucket ID')
@click.option('--name', '-n', help='New channel name')
@click.option('--url', '-u', help='New stream URL')
@click.option('--record', '-r', type=int, help='Record duration in hours')
@click.option('--timeshift', '-t', type=int, help='Timeshift duration in hours')
@click.pass_context
def update_channel(ctx, channel_id, bucket_id, name, url, record, timeshift):
    """Update a channel
    
    Examples:
        acrcloud buckets channels update 67890 --bucket-id 12345 --name "New Name"
    """
    api = ctx.obj['api']
    
    try:
        result = api.update_channel(
            bucket_id=bucket_id,
            channel_id=channel_id,
            name=name,
            url=url,
            record=record,
            timeshift=timeshift
        )
        
        click.echo(f"✓ Channel {channel_id} updated successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@channels.command(name='delete')
@click.argument('channel_id', type=int)
@click.option('--bucket-id', '-b', required=True, type=int, help='Bucket ID')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_channel(ctx, channel_id, bucket_id, yes):
    """Delete a channel
    
    Examples:
        acrcloud buckets channels delete 67890 --bucket-id 12345
        acrcloud buckets channels delete 67890 -b 12345 --yes
    """
    api = ctx.obj['api']
    
    if not yes:
        if not confirm_action(f"Are you sure you want to delete channel {channel_id}?"):
            click.echo("Cancelled")
            return
    
    try:
        api.delete_channel(bucket_id=bucket_id, channel_id=channel_id)
        click.echo(f"✓ Channel {channel_id} deleted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
