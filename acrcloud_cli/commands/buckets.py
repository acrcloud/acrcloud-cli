"""
Buckets command for ACRCloud CLI
"""

import click
import json
from ..api import ACRCloudAPI
from ..utils import output_json, output_table, confirm_action


@click.group(name='buckets')
@click.pass_context
def buckets(ctx):
    """Manage ACRCloud buckets"""
    ctx.obj['api'] = ACRCloudAPI(
        ctx.obj['access_token'],
        ctx.obj['base_url']
    )


@buckets.command(name='list')
@click.option('--page', '-p', default=1, help='Page number')
@click.option('--per-page', '-n', default=20, help='Results per page')
@click.option('--region', '-r', help='Filter by region (eu-west-1, us-west-2, ap-southeast-1)')
@click.option('--type', '-t', 'bucket_type', help='Filter by type (File, Live, LiveRec, LiveTimeshift)')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list_buckets(ctx, page, per_page, region, bucket_type, output):
    """List all buckets
    
    Examples:
        acrcloud buckets list
        acrcloud buckets list --region eu-west-1
        acrcloud buckets list --type File --output json
    """
    api = ctx.obj['api']
    
    try:
        result = api.list_buckets(page=page, per_page=per_page, 
                                  region=region, bucket_type=bucket_type)
        
        if output == 'json':
            output_json(result)
        else:
            buckets_data = result.get('data', [])
            if not buckets_data:
                click.echo("No buckets found")
                return
            
            headers = ['ID', 'Name', 'Type', 'Region', 'Files', 'Labels']
            rows = []
            for bucket in buckets_data:
                labels = ', '.join(bucket.get('labels', [])) or '-'
                rows.append([
                    bucket.get('id'),
                    bucket.get('name'),
                    bucket.get('type'),
                    bucket.get('region'),
                    bucket.get('num', 0),
                    labels
                ])
            output_table(headers, rows)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@buckets.command(name='get')
@click.argument('bucket_id', type=int)
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def get_bucket(ctx, bucket_id, output):
    """Get bucket details
    
    Examples:
        acrcloud buckets get 12345
        acrcloud buckets get 12345 --output json
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_bucket(bucket_id)
        
        if output == 'json':
            output_json(result)
        else:
            bucket = result.get('data', {})
            if not bucket:
                click.echo("Bucket not found")
                return
            
            click.echo(f"Bucket Details (ID: {bucket_id}):")
            click.echo("-" * 40)
            click.echo(f"  Name: {bucket.get('name')}")
            click.echo(f"  Type: {bucket.get('type')}")
            click.echo(f"  Region: {bucket.get('region')}")
            click.echo(f"  Files: {bucket.get('num', 0)}")
            click.echo(f"  Size: {bucket.get('size', 0)}")
            click.echo(f"  Labels: {', '.join(bucket.get('labels', [])) or '-'}")
            click.echo(f"  State: {'Active' if bucket.get('state') == 1 else 'Inactive'}")
            click.echo(f"  Created: {bucket.get('created_at')}")
            click.echo(f"  Updated: {bucket.get('updated_at')}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@buckets.command(name='create')
@click.option('--name', '-n', required=True, help='Bucket name')
@click.option('--type', '-t', 'bucket_type', default='File', 
              type=click.Choice(['File', 'Live', 'LiveRec', 'LiveTimeshift']),
              help='Bucket type')
@click.option('--region', '-r', required=True,
              type=click.Choice(['eu-west-1', 'us-west-2', 'ap-southeast-1']),
              help='Region')
@click.option('--net-type', type=click.Choice(['0', '1', '2']), default='1',
              help='Network type (0=public, 1=private, 2=both)')
@click.option('--labels', '-l', help='Labels (comma-separated)')
@click.option('--metadata-template', '-m', help='Metadata template (JSON string)')
@click.pass_context
def create_bucket(ctx, name, bucket_type, region, net_type, labels, metadata_template):
    """Create a new bucket
    
    Examples:
        acrcloud buckets create --name my-bucket --type File --region eu-west-1
        acrcloud buckets create -n music -t File -r ap-southeast-1 -l "Music,Audio"
    """
    api = ctx.obj['api']
    
    labels_list = [l.strip() for l in labels.split(',')] if labels else None
    
    try:
        result = api.create_bucket(
            name=name,
            bucket_type=bucket_type,
            region=region,
            net_type=int(net_type),
            labels=labels_list,
            metadata_template=metadata_template
        )
        
        bucket = result.get('data', {})
        click.echo(f"✓ Bucket created successfully!")
        click.echo(f"  ID: {bucket.get('id')}")
        click.echo(f"  Name: {bucket.get('name')}")
        click.echo(f"  Type: {bucket.get('type')}")
        click.echo(f"  Region: {bucket.get('region')}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@buckets.command(name='update')
@click.argument('bucket_id', type=int)
@click.option('--name', '-n', help='New bucket name')
@click.option('--labels', '-l', help='Labels (comma-separated)')
@click.option('--metadata-template', '-m', help='Metadata template (JSON string)')
@click.pass_context
def update_bucket(ctx, bucket_id, name, labels, metadata_template):
    """Update a bucket
    
    Examples:
        acrcloud buckets update 12345 --name new-name
        acrcloud buckets update 12345 -l "Music,Pop,Rock"
    """
    api = ctx.obj['api']
    
    labels_list = [l.strip() for l in labels.split(',')] if labels else None
    
    try:
        result = api.update_bucket(
            bucket_id=bucket_id,
            name=name,
            labels=labels_list,
            metadata_template=metadata_template
        )
        
        click.echo(f"✓ Bucket {bucket_id} updated successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@buckets.command(name='delete')
@click.argument('bucket_id', type=int)
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_bucket(ctx, bucket_id, yes):
    """Delete a bucket
    
    Examples:
        acrcloud buckets delete 12345
        acrcloud buckets delete 12345 --yes
    """
    api = ctx.obj['api']
    
    if not yes:
        if not confirm_action(f"Are you sure you want to delete bucket {bucket_id}?"):
            click.echo("Cancelled")
            return
    
    try:
        api.delete_bucket(bucket_id)
        click.echo(f"✓ Bucket {bucket_id} deleted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
