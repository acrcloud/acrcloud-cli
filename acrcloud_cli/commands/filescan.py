"""
File Scanning command for ACRCloud CLI
"""

import click
import json
from ..api import ACRCloudAPI
from ..utils import output_json, output_table, confirm_action


@click.group(name='filescan')
@click.pass_context
def filescan(ctx):
    """Manage ACRCloud File Scanning containers and files"""
    ctx.obj['api'] = ACRCloudAPI(
        ctx.obj['access_token'],
        ctx.obj['base_url']
    )


# ==================== FS Containers ====================

@filescan.command(name='list-containers')
@click.option('--page', '-p', default=1, help='Page number')
@click.option('--per-page', '-n', default=20, help='Results per page')
@click.option('--region', '-r', help='Filter by region (eu-west-1, us-west-2, ap-southeast-1)')
@click.option('--name', help='Search by name')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list_containers(ctx, page, per_page, region, name, output):
    """List all file scanning containers
    
    Examples:
        acrcloud filescan list-containers
        acrcloud filescan list-containers --region eu-west-1
    """
    api = ctx.obj['api']
    
    try:
        result = api.list_fs_containers(page=page, per_page=per_page, region=region, name=name)
        
        if output == 'json':
            output_json(result)
        else:
            containers = result.get('data', [])
            if not containers:
                click.echo("No containers found")
                return
            
            headers = ['ID', 'Name', 'Region', 'Audio Type', 'Engine', 'Files']
            rows = []
            for container in containers:
                rows.append([
                    container.get('id'),
                    container.get('name', '-')[:25],
                    container.get('region', '-'),
                    container.get('audio_type', '-'),
                    container.get('engine', '-'),
                    container.get('num', 0)
                ])
            output_table(headers, rows)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@filescan.command(name='get-container')
@click.argument('container_id', type=int)
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def get_container(ctx, container_id, output):
    """Get file scanning container details
    
    Examples:
        acrcloud filescan get-container 12345
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_fs_container(container_id)
        
        if output == 'json':
            output_json(result)
        else:
            container = result.get('data', {})
            if not container:
                click.echo("Container not found")
                return
            
            click.echo(f"Container Details (ID: {container_id}):")
            click.echo("-" * 40)
            click.echo(f"  Name: {container.get('name')}")
            click.echo(f"  Region: {container.get('region')}")
            click.echo(f"  Audio Type: {container.get('audio_type')}")
            click.echo(f"  Engine: {container.get('engine')}")
            click.echo(f"  Files: {container.get('num', 0)}")
            click.echo(f"  Size: {container.get('size', 0)}")
            click.echo(f"  Policy: {json.dumps(container.get('policy', {}))}")
            click.echo(f"  Buckets: {', '.join([str(b.get('id')) for b in container.get('buckets', [])])}")
            click.echo(f"  Created: {container.get('created_at')}")
            click.echo(f"  Updated: {container.get('updated_at')}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@filescan.command(name='create-container')
@click.option('--name', '-n', required=True, help='Container name')
@click.option('--region', '-r', required=True,
              type=click.Choice(['eu-west-1', 'us-west-2', 'ap-southeast-1']),
              help='Region')
@click.option('--audio-type', type=click.Choice(['linein', 'recorded']), default='linein',
              help='Audio type')
@click.option('--buckets', '-b', required=True, help='Bucket IDs (comma-separated or JSON array)')
@click.option('--engine', '-e', required=True, type=click.Choice(['1', '2', '3', '4']),
              help='Engine (1:Audio Fingerprinting, 2:Cover Songs, 3:Both, 4:Speech to Text)')
@click.option('--policy-type', required=True, type=click.Choice(['traverse', 'points']),
              help='Policy type')
@click.option('--interval', type=int, default=0, help='Interval for traverse policy')
@click.option('--rec-length', type=int, default=10, help='Recording length for traverse policy')
@click.option('--points', type=int, help='Number of points for points policy')
@click.option('--callback-url', '-c', help='Result callback URL')
@click.option('--deepright', type=click.Choice(['0', '1']), help='Enable derivative works detection')
@click.option('--music-detection', type=click.Choice(['0', '1']), help='Enable music/speech detection')
@click.option('--ai-detection', type=click.Choice(['0', '1']), help='Enable AI detection')
@click.pass_context
def create_container(ctx, name, region, audio_type, buckets, engine, policy_type,
                     interval, rec_length, points, callback_url, deepright,
                     music_detection, ai_detection):
    """Create a new file scanning container
    
    Examples:
        acrcloud filescan create-container --name my-container --region eu-west-1 \\
            --buckets "[12345,67890]" --engine 1 --policy-type traverse
    """
    api = ctx.obj['api']
    
    # Parse buckets
    try:
        buckets_list = json.loads(buckets) if buckets.startswith('[') else [int(b.strip()) for b in buckets.split(',')]
    except:
        buckets_list = [buckets]
    
    # Build policy
    policy = {'type': policy_type}
    if policy_type == 'traverse':
        policy['interval'] = interval
        policy['rec_length'] = rec_length
    else:
        policy['points'] = points if points else 3
    
    try:
        result = api.create_fs_container(
            name=name,
            region=region,
            audio_type=audio_type,
            buckets=buckets_list,
            engine=int(engine),
            policy=policy,
            callback_url=callback_url,
            deepright=deepright == '1' if deepright else None,
            music_detection=music_detection == '1' if music_detection else None,
            ai_detection=ai_detection == '1' if ai_detection else None
        )
        
        container = result.get('data', {})
        click.echo(f"✓ Container created successfully!")
        click.echo(f"  ID: {container.get('id')}")
        click.echo(f"  Name: {container.get('name')}")
        click.echo(f"  Region: {container.get('region')}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@filescan.command(name='update-container')
@click.argument('container_id', type=int)
@click.option('--name', '-n', help='Container name')
@click.option('--audio-type', type=click.Choice(['linein', 'recorded']), help='Audio type')
@click.option('--buckets', '-b', help='Bucket IDs (comma-separated or JSON array)')
@click.option('--engine', '-e', type=click.Choice(['1', '2', '3', '4']),
              help='Engine (1:Audio Fingerprinting, 2:Cover Songs, 3:Both, 4:Speech to Text)')
@click.option('--callback-url', '-c', help='Result callback URL')
@click.option('--deepright', type=click.Choice(['0', '1']), help='Enable derivative works detection')
@click.option('--music-detection', type=click.Choice(['0', '1']), help='Enable music/speech detection')
@click.option('--ai-detection', type=click.Choice(['0', '1']), help='Enable AI detection')
@click.pass_context
def update_container(ctx, container_id, name, audio_type, buckets, engine,
                     callback_url, deepright, music_detection, ai_detection):
    """Update a file scanning container
    
    Examples:
        acrcloud filescan update-container 12345 --name new-name
    """
    api = ctx.obj['api']
    
    # Parse buckets
    buckets_list = None
    if buckets:
        try:
            buckets_list = json.loads(buckets) if buckets.startswith('[') else [int(b.strip()) for b in buckets.split(',')]
        except:
            buckets_list = [buckets]
    
    try:
        result = api.update_fs_container(
            container_id=container_id,
            name=name,
            audio_type=audio_type,
            buckets=buckets_list,
            engine=int(engine) if engine else None,
            callback_url=callback_url,
            deepright=deepright == '1' if deepright else None,
            music_detection=music_detection == '1' if music_detection else None,
            ai_detection=ai_detection == '1' if ai_detection else None
        )
        
        click.echo(f"✓ Container {container_id} updated successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@filescan.command(name='delete-container')
@click.argument('container_id', type=int)
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_container(ctx, container_id, yes):
    """Delete a file scanning container
    
    Examples:
        acrcloud filescan delete-container 12345
        acrcloud filescan delete-container 12345 --yes
    """
    api = ctx.obj['api']
    
    if not yes:
        if not confirm_action(f"Are you sure you want to delete container {container_id}?"):
            click.echo("Cancelled")
            return
    
    try:
        api.delete_fs_container(container_id)
        click.echo(f"✓ Container {container_id} deleted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# ==================== FS Files ====================

@filescan.command(name='list-files')
@click.option('--container-id', '-c', required=True, type=int, help='Container ID')
@click.option('--region', '-r', required=True, help='Container region')
@click.option('--page', '-p', default=1, help='Page number')
@click.option('--per-page', '-n', default=20, help='Results per page')
@click.option('--search', '-s', help='Search by name or URI')
@click.option('--with-result', type=click.Choice(['0', '1']), help='Include results')
@click.option('--state', help='Filter by state (0:processing, 1:Ready, -1:No results, -2/-3:Error)')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list_files(ctx, container_id, region, page, per_page, search, with_result, state, output):
    """List files in a file scanning container
    
    Examples:
        acrcloud filescan list-files --container-id 12345 --region eu-west-1
    """
    api = ctx.obj['api']
    
    try:
        result = api.list_fs_files(
            container_id=container_id,
            region=region,
            page=page,
            per_page=per_page,
            search=search,
            with_result=int(with_result) if with_result else None,
            state=state
        )
        
        if output == 'json':
            output_json(result)
        else:
            files = result.get('data', [])
            if not files:
                click.echo("No files found")
                return
            
            headers = ['ID', 'Name', 'Type', 'Duration', 'State']
            rows = []
            for f in files:
                state_map = {'0': 'Processing', '1': 'Ready', '-1': 'No results', '-2': 'Error', '-3': 'Error'}
                rows.append([
                    f.get('id', '-')[:20],
                    f.get('name', '-')[:30],
                    f.get('data_type', '-'),
                    f.get('duration', '-'),
                    state_map.get(str(f.get('state')), f.get('state'))
                ])
            output_table(headers, rows)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@filescan.command(name='get-file')
@click.argument('file_id')
@click.option('--container-id', '-c', required=True, type=int, help='Container ID')
@click.option('--region', '-r', required=True, help='Container region')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='json', help='Output format')
@click.pass_context
def get_file(ctx, file_id, container_id, region, output):
    """Get file scanning file details with results
    
    Examples:
        acrcloud filescan get-file FILE_ID --container-id 12345 --region eu-west-1
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_fs_file(container_id=container_id, region=region, file_id=file_id)
        
        if output == 'json':
            output_json(result)
        else:
            file_data = result.get('data', [])
            if not file_data:
                click.echo("File not found")
                return
            
            # Handle both single file and array response
            if isinstance(file_data, list) and len(file_data) > 0:
                file_info = file_data[0]
            else:
                file_info = file_data
            
            click.echo(f"File Details (ID: {file_id}):")
            click.echo("-" * 40)
            click.echo(f"  Name: {file_info.get('name')}")
            click.echo(f"  Type: {file_info.get('data_type')}")
            click.echo(f"  Duration: {file_info.get('duration', '-')}s")
            click.echo(f"  URI: {file_info.get('uri', '-')}")
            click.echo(f"  State: {file_info.get('state')}")
            click.echo(f"  Created: {file_info.get('created_at')}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@filescan.command(name='upload')
@click.option('--container-id', '-c', required=True, type=int, help='Container ID')
@click.option('--region', '-r', required=True, help='Container region')
@click.option('--file', '-f', 'file_path', type=click.Path(exists=True), help='Audio file path')
@click.option('--audio-url', '-u', help='Audio URL')
@click.option('--type', '-t', 'data_type', default='audio',
              type=click.Choice(['audio', 'audio_url']),
              help='Upload type')
@click.pass_context
def upload_file(ctx, container_id, region, file_path, audio_url, data_type):
    """Upload a file to file scanning container
    
    Examples:
        acrcloud filescan upload --container-id 12345 --region eu-west-1 --file audio.mp3
        acrcloud filescan upload -c 12345 -r eu-west-1 -u https://example.com/audio.mp3 -t audio_url
    """
    api = ctx.obj['api']
    
    try:
        result = api.upload_fs_file(
            container_id=container_id,
            region=region,
            file_path=file_path,
            audio_url=audio_url,
            data_type=data_type
        )
        
        file_data = result.get('data', {})
        click.echo(f"✓ File uploaded successfully!")
        if isinstance(file_data, dict):
            click.echo(f"  ID: {file_data.get('id')}")
            click.echo(f"  Name: {file_data.get('name')}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@filescan.command(name='delete-files')
@click.option('--container-id', '-c', required=True, type=int, help='Container ID')
@click.option('--region', '-r', required=True, help='Container region')
@click.option('--file-ids', '-i', required=True, help='Comma-separated file IDs')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_files(ctx, container_id, region, file_ids, yes):
    """Delete files from file scanning container
    
    Examples:
        acrcloud filescan delete-files --container-id 12345 --region eu-west-1 --file-ids "id1,id2"
    """
    api = ctx.obj['api']
    
    if not yes:
        if not confirm_action(f"Are you sure you want to delete these files?"):
            click.echo("Cancelled")
            return
    
    try:
        api.delete_fs_files(container_id=container_id, region=region, file_ids=file_ids)
        click.echo(f"✓ Files deleted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@filescan.command(name='rescan')
@click.option('--container-id', '-c', required=True, type=int, help='Container ID')
@click.option('--region', '-r', required=True, help='Container region')
@click.option('--file-ids', '-i', required=True, help='Comma-separated file IDs')
@click.pass_context
def rescan_files(ctx, container_id, region, file_ids):
    """Rescan files in file scanning container
    
    Examples:
        acrcloud filescan rescan --container-id 12345 --region eu-west-1 --file-ids "id1,id2"
    """
    api = ctx.obj['api']
    
    try:
        result = api.rescan_fs_files(container_id=container_id, region=region, file_ids=file_ids)
        click.echo(f"✓ Files rescanned successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
