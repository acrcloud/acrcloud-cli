"""
BM Projects command for ACRCloud CLI
"""

import click
import json
from ..api import ACRCloudAPI
from ..utils import output_json, output_table, confirm_action


@click.group(name='bmprojects')
@click.pass_context
def bmprojects(ctx):
    """Manage ACRCloud BM (Broadcast Monitoring) Custom Streams Projects"""
    ctx.obj['api'] = ACRCloudAPI(
        ctx.obj['access_token'],
        ctx.obj['base_url']
    )


# ==================== BM Custom Streams Projects ====================

@bmprojects.command(name='list')
@click.option('--page', '-p', default=1, help='Page number')
@click.option('--per-page', '-n', default=20, help='Results per page')
@click.option('--region', '-r', help='Filter by region (eu-west-1, us-west-2, ap-southeast-1)')
@click.option('--type', '-t', 'project_type', help='Filter by type (BM-ACRC, BM-LOCAL)')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list_projects(ctx, page, per_page, region, project_type, output):
    """List all BM custom streams projects
    
    Examples:
        acrcloud bmprojects list
        acrcloud bmprojects list --region eu-west-1
    """
    api = ctx.obj['api']
    
    try:
        result = api.list_bm_cs_projects(page=page, per_page=per_page, region=region, types=project_type)
        
        if output == 'json':
            output_json(result)
        else:
            projects = result.get('data', [])
            if not projects:
                click.echo("No projects found")
                return
            
            headers = ['ID', 'Name', 'Type', 'Region', 'State', 'Streams']
            rows = []
            for project in projects:
                rows.append([
                    project.get('id'),
                    project.get('name', '-')[:25],
                    project.get('type', '-'),
                    project.get('region', '-'),
                    'Active' if project.get('state') == 1 else 'Inactive',
                    project.get('monitoring_num', 0)
                ])
            output_table(headers, rows)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bmprojects.command(name='get')
@click.argument('project_id', type=int)
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def get_project(ctx, project_id, output):
    """Get BM custom streams project details
    
    Examples:
        acrcloud bmprojects get 12345
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_bm_cs_project(project_id)
        
        if output == 'json':
            output_json(result)
        else:
            project = result.get('data', {})
            if not project:
                click.echo("Project not found")
                return
            
            click.echo(f"Project Details (ID: {project_id}):")
            click.echo("-" * 40)
            click.echo(f"  Name: {project.get('name')}")
            click.echo(f"  Type: {project.get('type')}")
            click.echo(f"  Region: {project.get('region')}")
            click.echo(f"  Access Key: {project.get('access_key')}")
            click.echo(f"  Buckets: {project.get('bucket_group', '-')}")
            click.echo(f"  External IDs: {', '.join(project.get('external_ids', [])) or '-'}")
            click.echo(f"  State: {'Active' if project.get('state') == 1 else 'Inactive'}")
            click.echo(f"  Monitoring: {project.get('monitoring_num', 0)} streams")
            click.echo(f"  Created: {project.get('created_at')}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bmprojects.command(name='create')
@click.option('--name', '-n', required=True, help='Project name')
@click.option('--region', '-r', required=True,
              type=click.Choice(['eu-west-1', 'us-west-2', 'ap-southeast-1']),
              help='Region')
@click.option('--buckets', '-b', required=True, help='Bucket IDs (comma-separated)')
@click.option('--type', '-t', 'project_type', default='BM-ACRC',
              type=click.Choice(['BM-ACRC', 'BM-LOCAL']),
              help='Project type (BM-ACRC: server-side, BM-LOCAL: local monitoring)')
@click.option('--external-ids', '-e', help='External IDs (spotify,deezer,isrc,upc,musicbrainz)')
@click.option('--metadata-template', '-m', help='Metadata template')
@click.pass_context
def create_project(ctx, name, region, buckets, project_type, external_ids, metadata_template):
    """Create a new BM custom streams project
    
    Examples:
        acrcloud bmprojects create --name my-bm-project --region eu-west-1 --buckets "12345,67890"
    """
    api = ctx.obj['api']
    
    # Parse buckets
    try:
        buckets_list = [int(b.strip()) for b in buckets.split(',')]
    except:
        buckets_list = [buckets]
    
    try:
        result = api.create_bm_cs_project(
            name=name,
            region=region,
            buckets=buckets_list,
            project_type=project_type,
            external_ids=external_ids,
            metadata_template=metadata_template
        )
        
        project = result.get('data', {})
        click.echo(f"✓ Project created successfully!")
        click.echo(f"  ID: {project.get('id')}")
        click.echo(f"  Name: {project.get('name')}")
        click.echo(f"  Type: {project.get('type')}")
        click.echo(f"  Access Key: {project.get('access_key')}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bmprojects.command(name='update')
@click.argument('project_id', type=int)
@click.option('--name', '-n', help='Project name')
@click.option('--buckets', '-b', help='Bucket IDs (comma-separated)')
@click.option('--external-ids', '-e', help='External IDs (comma-separated)')
@click.option('--metadata-template', '-m', help='Metadata template')
@click.pass_context
def update_project(ctx, project_id, name, buckets, external_ids, metadata_template):
    """Update a BM custom streams project
    
    Examples:
        acrcloud bmprojects update 12345 --name new-name
    """
    api = ctx.obj['api']
    
    # Parse buckets
    buckets_list = None
    if buckets:
        try:
            buckets_list = [int(b.strip()) for b in buckets.split(',')]
        except:
            buckets_list = [buckets]
    
    # Parse external IDs
    external_ids_list = None
    if external_ids:
        external_ids_list = [e.strip() for e in external_ids.split(',')]
    
    try:
        result = api.update_bm_cs_project(
            project_id=project_id,
            name=name,
            buckets=buckets_list,
            external_ids=external_ids_list,
            metadata_template=metadata_template
        )
        
        click.echo(f"✓ Project {project_id} updated successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bmprojects.command(name='delete')
@click.argument('project_id', type=int)
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_project(ctx, project_id, yes):
    """Delete a BM custom streams project
    
    Examples:
        acrcloud bmprojects delete 12345
        acrcloud bmprojects delete 12345 --yes
    """
    api = ctx.obj['api']
    
    if not yes:
        if not confirm_action(f"Are you sure you want to delete project {project_id}?"):
            click.echo("Cancelled")
            return
    
    try:
        api.delete_bm_cs_project(project_id)
        click.echo(f"✓ Project {project_id} deleted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bmprojects.command(name='set-callback')
@click.argument('project_id', type=int)
@click.option('--url', '-u', required=True, help='Callback URL')
@click.pass_context
def set_callback(ctx, project_id, url):
    """Set result callback URL for BM custom streams project
    
    Examples:
        acrcloud bmprojects set-callback 12345 --url https://callback.example.com/results
    """
    api = ctx.obj['api']
    
    try:
        result = api.set_bm_cs_result_callback(project_id=project_id, callback_url=url)
        click.echo(f"✓ Callback URL set successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# ==================== BM Streams ====================

@bmprojects.command(name='list-streams')
@click.argument('project_id', type=int)
@click.option('--page', '-p', default=1, help='Page number')
@click.option('--per-page', '-n', default=50, help='Results per page')
@click.option('--state', '-s', help='Filter by state (Running, Timeout, Paused, Invalid URL, Mute, Other)')
@click.option('--search', help='Search by name, stream ID, URL, user-defined, or remark')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list_streams(ctx, project_id, page, per_page, state, search, output):
    """List streams in a BM custom streams project
    
    Examples:
        acrcloud bmprojects list-streams 12345
        acrcloud bmprojects list-streams 12345 --state Running
    """
    api = ctx.obj['api']
    
    try:
        result = api.list_bm_streams(
            project_id=project_id,
            page=page,
            per_page=per_page,
            state=state,
            search_value=search
        )
        
        if output == 'json':
            output_json(result)
        else:
            streams = result.get('data', [])
            if not streams:
                click.echo("No streams found")
                return
            
            headers = ['Stream ID', 'Name', 'State', 'Type', 'URL']
            rows = []
            for stream in streams:
                urls = stream.get('stream_urls', [])
                url_display = urls[0][:30] + '...' if urls and len(urls[0]) > 30 else (urls[0] if urls else '-')
                rows.append([
                    stream.get('stream_id', '-')[:15],
                    stream.get('name', '-')[:20],
                    stream.get('state', '-'),
                    stream.get('stream_type', '-'),
                    url_display
                ])
            output_table(headers, rows)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bmprojects.command(name='add-stream')
@click.argument('project_id', type=int)
@click.option('--name', '-n', required=True, help='Stream name')
@click.option('--url', '-u', required=True, help='Stream URL')
@click.option('--config-id', '-c', required=True, type=int, help='Config ID')
@click.option('--user-defined', '-d', help='User-defined metadata')
@click.pass_context
def add_stream(ctx, project_id, name, url, config_id, user_defined):
    """Add a stream to BM custom streams project
    
    Examples:
        acrcloud bmprojects add-stream 12345 --name "Radio One" --url "http://stream.example.com" --config-id 1
    """
    api = ctx.obj['api']
    
    try:
        result = api.add_bm_stream(
            project_id=project_id,
            stream_urls=[url],
            name=name,
            config_id=config_id,
            user_defined=user_defined
        )
        
        stream = result.get('data', {})
        click.echo(f"✓ Stream added successfully!")
        click.echo(f"  Stream ID: {stream.get('stream_id')}")
        click.echo(f"  Name: {stream.get('name')}")
        click.echo(f"  State: {stream.get('state')}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bmprojects.command(name='update-stream')
@click.argument('project_id', type=int)
@click.argument('stream_id')
@click.option('--name', '-n', help='Stream name')
@click.option('--url', '-u', help='Stream URL')
@click.option('--config-id', '-c', type=int, help='Config ID')
@click.pass_context
def update_stream(ctx, project_id, stream_id, name, url, config_id):
    """Update a stream in BM custom streams project
    
    Examples:
        acrcloud bmprojects update-stream 12345 s-ABC123 --name "New Name"
    """
    api = ctx.obj['api']
    
    stream_urls = [url] if url else None
    
    try:
        result = api.update_bm_stream(
            project_id=project_id,
            stream_id=stream_id,
            stream_urls=stream_urls,
            name=name,
            config_id=config_id
        )
        
        click.echo(f"✓ Stream {stream_id} updated successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bmprojects.command(name='delete-streams')
@click.argument('project_id', type=int)
@click.option('--stream-ids', '-i', required=True, help='Comma-separated stream IDs')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_streams(ctx, project_id, stream_ids, yes):
    """Delete streams from BM custom streams project
    
    Examples:
        acrcloud bmprojects delete-streams 12345 --stream-ids "s-ABC123,s-DEF456"
    """
    api = ctx.obj['api']
    
    if not yes:
        if not confirm_action(f"Are you sure you want to delete these streams?"):
            click.echo("Cancelled")
            return
    
    try:
        api.delete_bm_streams(project_id=project_id, stream_ids=stream_ids)
        click.echo(f"✓ Streams deleted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bmprojects.command(name='pause-streams')
@click.argument('project_id', type=int)
@click.option('--stream-ids', '-i', required=True, help='Comma-separated stream IDs')
@click.pass_context
def pause_streams(ctx, project_id, stream_ids):
    """Pause streams in BM custom streams project
    
    Examples:
        acrcloud bmprojects pause-streams 12345 --stream-ids "s-ABC123,s-DEF456"
    """
    api = ctx.obj['api']
    
    try:
        api.pause_bm_streams(project_id=project_id, stream_ids=stream_ids)
        click.echo(f"✓ Streams paused successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bmprojects.command(name='restart-streams')
@click.argument('project_id', type=int)
@click.option('--stream-ids', '-i', required=True, help='Comma-separated stream IDs')
@click.pass_context
def restart_streams(ctx, project_id, stream_ids):
    """Restart streams in BM custom streams project
    
    Examples:
        acrcloud bmprojects restart-streams 12345 --stream-ids "s-ABC123,s-DEF456"
    """
    api = ctx.obj['api']
    
    try:
        api.restart_bm_streams(project_id=project_id, stream_ids=stream_ids)
        click.echo(f"✓ Streams restarted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
