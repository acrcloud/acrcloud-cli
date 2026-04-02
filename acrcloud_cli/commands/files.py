"""
Files command for ACRCloud CLI
"""

import click
import json
from ..api import ACRCloudAPI
from ..utils import output_json, output_table, confirm_action


@click.group(name='files')
@click.pass_context
def files(ctx):
    """Manage audio files in buckets"""
    ctx.obj['api'] = ACRCloudAPI(
        ctx.obj['access_token'],
        ctx.obj['base_url']
    )


@files.command(name='list')
@click.option('--bucket-id', '-b', required=True, type=int, help='Bucket ID')
@click.option('--page', '-p', default=1, help='Page number')
@click.option('--per-page', '-n', default=20, help='Results per page')
@click.option('--keyword', '-k', help='Search keyword')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list_files(ctx, bucket_id, page, per_page, keyword, output):
    """List files in a bucket
    
    Examples:
        acrcloud buckets files list --bucket-id 12345
        acrcloud buckets files list -b 12345 --keyword "song"
    """
    api = ctx.obj['api']
    
    try:
        result = api.list_files(bucket_id=bucket_id, page=page, 
                                per_page=per_page, keyword=keyword)
        
        if output == 'json':
            output_json(result)
        else:
            files_data = result.get('data', [])
            if not files_data:
                click.echo("No files found")
                return
            
            headers = ['ID', 'ACRID', 'Title', 'Duration', 'State']
            rows = []
            for file in files_data:
                rows.append([
                    file.get('id'),
                    file.get('acr_id', '-')[:20] + '...' if file.get('acr_id') and len(file.get('acr_id')) > 20 else file.get('acr_id', '-'),
                    file.get('title', '-')[:30],
                    f"{float(file.get('duration', 0)):.2f}s" if file.get('duration') else '-',
                    'Active' if file.get('state') == 1 else 'Processing' if file.get('state') == 0 else 'Inactive'
                ])
            output_table(headers, rows)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@files.command(name='get')
@click.argument('file_id', type=int)
@click.option('--bucket-id', '-b', required=True, type=int, help='Bucket ID')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def get_file(ctx, file_id, bucket_id, output):
    """Get file details
    
    Examples:
        acrcloud buckets files get 67890 --bucket-id 12345
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_file(bucket_id=bucket_id, file_id=file_id)
        
        if output == 'json':
            output_json(result)
        else:
            file_data = result.get('data', {})
            if not file_data:
                click.echo("File not found")
                return
            
            click.echo(f"File Details (ID: {file_id}):")
            click.echo("-" * 40)
            click.echo(f"  ACRID: {file_data.get('acr_id')}")
            click.echo(f"  Title: {file_data.get('title', '-')}")
            click.echo(f"  Duration: {file_data.get('duration', '-')}s")
            click.echo(f"  State: {'Active' if file_data.get('state') == 1 else 'Processing' if file_data.get('state') == 0 else 'Inactive'}")
            click.echo(f"  User Defined: {json.dumps(file_data.get('user_defined', {}))}")
            click.echo(f"  Created: {file_data.get('created_at')}")
            click.echo(f"  Updated: {file_data.get('updated_at')}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@files.command(name='upload')
@click.option('--bucket-id', '-b', required=True, type=int, help='Bucket ID')
@click.option('--file', '-f', 'file_path', type=click.Path(exists=True), help='Audio or fingerprint file path')
@click.option('--audio-url', '-u', help='Audio file URL (for audio_url type)')
@click.option('--acrid', '-a', help='ACRID from ACRCloud Music Database')
@click.option('--type', '-t', 'data_type', default='audio',
              type=click.Choice(['audio', 'fingerprint', 'audio_url', 'acrid']),
              help='Upload type')
@click.option('--title', '-n', help='File title')
@click.option('--user-defined', '-d', help='User-defined metadata (JSON string)')
@click.pass_context
def upload_file(ctx, bucket_id, file_path, audio_url, acrid, data_type, title, user_defined):
    """Upload an audio file or fingerprint to a bucket
    
    Examples:
        acrcloud buckets files upload --bucket-id 12345 --file audio.mp3
        acrcloud buckets files upload -b 12345 -f fingerprint.fp -t fingerprint
        acrcloud buckets files upload -b 12345 -u https://example.com/audio.mp3 -t audio_url
        acrcloud buckets files upload -b 12345 -a "ACRID123" -t acrid
    """
    api = ctx.obj['api']
    
    user_defined_dict = json.loads(user_defined) if user_defined else None
    
    try:
        result = api.upload_file(
            bucket_id=bucket_id,
            file_path=file_path,
            title=title,
            data_type=data_type,
            audio_url=audio_url,
            acrid=acrid,
            user_defined=user_defined_dict
        )
        
        file_data = result.get('data', {})
        click.echo(f"✓ File uploaded successfully!")
        click.echo(f"  ID: {file_data.get('id')}")
        click.echo(f"  ACRID: {file_data.get('acr_id')}")
        click.echo(f"  Title: {file_data.get('title', '-')}")
        click.echo(f"  Duration: {file_data.get('duration', '-')}s")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@files.command(name='update')
@click.argument('file_id', type=int)
@click.option('--bucket-id', '-b', required=True, type=int, help='Bucket ID')
@click.option('--title', '-n', help='New title')
@click.option('--user-defined', '-d', help='User-defined metadata (JSON string)')
@click.pass_context
def update_file(ctx, file_id, bucket_id, title, user_defined):
    """Update a file
    
    Examples:
        acrcloud buckets files update 67890 --bucket-id 12345 --title "New Title"
    """
    api = ctx.obj['api']
    
    user_defined_dict = json.loads(user_defined) if user_defined else None
    
    try:
        result = api.update_file(
            bucket_id=bucket_id,
            file_id=file_id,
            title=title,
            user_defined=user_defined_dict
        )
        
        click.echo(f"✓ File {file_id} updated successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@files.command(name='delete')
@click.argument('file_id', type=int)
@click.option('--bucket-id', '-b', required=True, type=int, help='Bucket ID')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_file(ctx, file_id, bucket_id, yes):
    """Delete a file
    
    Examples:
        acrcloud buckets files delete 67890 --bucket-id 12345
        acrcloud buckets files delete 67890 -b 12345 --yes
    """
    api = ctx.obj['api']
    
    if not yes:
        if not confirm_action(f"Are you sure you want to delete file {file_id}?"):
            click.echo("Cancelled")
            return
    
    try:
        api.delete_file(bucket_id=bucket_id, file_id=file_id)
        click.echo(f"✓ File {file_id} deleted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@files.command(name='delete-batch')
@click.option('--bucket-id', '-b', required=True, type=int, help='Bucket ID')
@click.option('--file-ids', '-i', required=True, help='Comma-separated file IDs')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_files_batch(ctx, bucket_id, file_ids, yes):
    """Delete multiple files
    
    Examples:
        acrcloud buckets files delete-batch --bucket-id 12345 --file-ids "1,2,3"
    """
    api = ctx.obj['api']
    
    ids = [int(i.strip()) for i in file_ids.split(',')]
    
    if not yes:
        if not confirm_action(f"Are you sure you want to delete {len(ids)} files?"):
            click.echo("Cancelled")
            return
    
    try:
        api.delete_files_batch(bucket_id=bucket_id, file_ids=ids)
        click.echo(f"✓ {len(ids)} files deleted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@files.command(name='move')
@click.option('--bucket-id', '-b', required=True, type=int, help='Source bucket ID')
@click.option('--target-bucket-id', '-t', required=True, type=int, help='Target bucket ID')
@click.option('--file-ids', '-i', required=True, help='Comma-separated file IDs')
@click.pass_context
def move_files(ctx, bucket_id, target_bucket_id, file_ids):
    """Move files to another bucket
    
    Examples:
        acrcloud buckets files move --bucket-id 12345 --target-bucket-id 67890 --file-ids "1,2,3"
    """
    api = ctx.obj['api']
    
    ids = [int(i.strip()) for i in file_ids.split(',')]
    
    try:
        api.move_files(bucket_id=bucket_id, target_bucket_id=target_bucket_id, file_ids=ids)
        click.echo(f"✓ {len(ids)} files moved to bucket {target_bucket_id} successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@files.command(name='dump')
@click.option('--bucket-id', '-b', required=True, type=int, help='Bucket ID')
@click.pass_context
def dump_files(ctx, bucket_id):
    """Dump all files information in a bucket (once per day limit)
    
    Examples:
        acrcloud buckets files dump --bucket-id 12345
    """
    api = ctx.obj['api']
    
    try:
        result = api.dump_files(bucket_id=bucket_id)
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
