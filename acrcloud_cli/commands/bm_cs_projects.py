"""
BM Projects command for ACRCloud CLI
"""

import click
import json
from ..api import ACRCloudAPI
from ..utils import output_json, output_table, confirm_action


@click.group(name='bm-cs-projects')
@click.pass_context
def bm_cs_projects(ctx):
    """Manage ACRCloud BM (Broadcast Monitoring) Custom Streams Projects"""
    ctx.obj['api'] = ACRCloudAPI(
        ctx.obj['access_token'],
        ctx.obj['base_url']
    )


# ==================== BM Custom Streams Projects ====================

@bm_cs_projects.command(name='list')
@click.option('--page', '-p', default=1, help='Page number')
@click.option('--per-page', '-n', default=20, help='Results per page')
@click.option('--region', '-r', help='Filter by region (eu-west-1, us-west-2, ap-southeast-1)')
@click.option('--type', '-t', 'project_type', help='Filter by type (BM-ACRC, BM-LOCAL)')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list_projects(ctx, page, per_page, region, project_type, output):
    """List all BM custom streams projects
    
    Examples:
        acrcloud bm-cs-projects list
        acrcloud bm-cs-projects list --region eu-west-1
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


@bm_cs_projects.command(name='get')
@click.argument('project_id', type=int)
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def get_project(ctx, project_id, output):
    """Get BM custom streams project details
    
    Examples:
        acrcloud bm-cs-projects get 12345
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


@bm_cs_projects.command(name='create')
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
        acrcloud bm-cs-projects create --name my-bm-project --region eu-west-1 --buckets "12345,67890"
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


@bm_cs_projects.command(name='update')
@click.argument('project_id', type=int)
@click.option('--name', '-n', help='Project name')
@click.option('--buckets', '-b', help='Bucket IDs (comma-separated)')
@click.option('--external-ids', '-e', help='External IDs (comma-separated)')
@click.option('--metadata-template', '-m', help='Metadata template')
@click.pass_context
def update_project(ctx, project_id, name, buckets, external_ids, metadata_template):
    """Update a BM custom streams project
    
    Examples:
        acrcloud bm-cs-projects update 12345 --name new-name
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


@bm_cs_projects.command(name='delete')
@click.argument('project_id', type=int)
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_project(ctx, project_id, yes):
    """Delete a BM custom streams project
    
    Examples:
        acrcloud bm-cs-projects delete 12345
        acrcloud bm-cs-projects delete 12345 --yes
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


@bm_cs_projects.command(name='set-callback')
@click.argument('project_id', type=int)
@click.option('--url', '-u', required=True, help='Callback URL')
@click.pass_context
def set_callback(ctx, project_id, url):
    """Set result callback URL for BM custom streams project
    
    Examples:
        acrcloud bm-cs-projects set-callback 12345 --url https://callback.example.com/results
    """
    api = ctx.obj['api']
    
    try:
        result = api.set_bm_cs_result_callback(project_id=project_id, callback_url=url)
        click.echo(f"✓ Callback URL set successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_cs_projects.command(name='set-state-callback')
@click.argument('project_id', type=int)
@click.option('--email', '-e', help='State notification email')
@click.option('--frequency', '-f', type=click.Choice(['0', '1', '2']), help='Email frequency (0:High, 1:Low, 2:None)')
@click.option('--url', '-u', help='State notification URL')
@click.pass_context
def set_state_callback(ctx, project_id, email, frequency, url):
    """Set state notification callback for BM custom streams project
    
    Examples:
        acrcloud bm-cs-projects set-state-callback 12345 --email notify@example.com --frequency 0
        acrcloud bm-cs-projects set-state-callback 12345 --url https://callback.example.com/state
    """
    api = ctx.obj['api']
    
    freq_int = int(frequency) if frequency is not None else None
    
    if not email and frequency is None and not url:
        click.echo("Error: Please provide at least one of --email, --frequency, or --url", err=True)
        return
    
    try:
        api.set_bm_cs_state_notification_callback(
            project_id=project_id,
            email=email,
            frequency=freq_int,
            url=url
        )
        click.echo(f"✓ State notification callback set successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# ==================== BM Streams ====================

@bm_cs_projects.command(name='list-streams')
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
        acrcloud bm-cs-projects list-streams 12345
        acrcloud bm-cs-projects list-streams 12345 --state Running
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


@bm_cs_projects.command(name='add-stream')
@click.argument('project_id', type=int)
@click.option('--name', '-n', required=True, help='Stream name')
@click.option('--url', '-u', required=True, help='Stream URL')
@click.option('--config-id', '-c', required=True, type=int, help='Config ID')
@click.option('--user-defined', '-d', help='User-defined metadata')
@click.pass_context
def add_stream(ctx, project_id, name, url, config_id, user_defined):
    """Add a stream to BM custom streams project
    
    Examples:
        acrcloud bm-cs-projects add-stream 12345 --name "Radio One" --url "http://stream.example.com" --config-id 1
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


@bm_cs_projects.command(name='update-stream')
@click.argument('project_id', type=int)
@click.argument('stream_id')
@click.option('--name', '-n', help='Stream name')
@click.option('--url', '-u', help='Stream URL')
@click.option('--config-id', '-c', type=int, help='Config ID')
@click.pass_context
def update_stream(ctx, project_id, stream_id, name, url, config_id):
    """Update a stream in BM custom streams project
    
    Examples:
        acrcloud bm-cs-projects update-stream 12345 s-ABC123 --name "New Name"
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


@bm_cs_projects.command(name='delete-streams')
@click.argument('project_id', type=int)
@click.option('--stream-ids', '-i', required=True, help='Comma-separated stream IDs')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_streams(ctx, project_id, stream_ids, yes):
    """Delete streams from BM custom streams project
    
    Examples:
        acrcloud bm-cs-projects delete-streams 12345 --stream-ids "s-ABC123,s-DEF456"
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


@bm_cs_projects.command(name='pause-streams')
@click.argument('project_id', type=int)
@click.option('--stream-ids', '-i', required=True, help='Comma-separated stream IDs')
@click.pass_context
def pause_streams(ctx, project_id, stream_ids):
    """Pause streams in BM custom streams project
    
    Examples:
        acrcloud bm-cs-projects pause-streams 12345 --stream-ids "s-ABC123,s-DEF456"
    """
    api = ctx.obj['api']
    
    try:
        api.pause_bm_streams(project_id=project_id, stream_ids=stream_ids)
        click.echo(f"✓ Streams paused successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_cs_projects.command(name='restart-streams')
@click.argument('project_id', type=int)
@click.option('--stream-ids', '-i', required=True, help='Comma-separated stream IDs')
@click.pass_context
def restart_streams(ctx, project_id, stream_ids):
    """Restart streams in BM custom streams project
    
    Examples:
        acrcloud bm-cs-projects restart-streams 12345 --stream-ids "s-ABC123,s-DEF456"
    """
    api = ctx.obj['api']
    
    try:
        api.restart_bm_streams(project_id=project_id, stream_ids=stream_ids)
        click.echo(f"✓ Streams restarted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# ==================== BM Custom Streams Data ====================

@bm_cs_projects.command(name='stream-state')
@click.argument('project_id', type=int)
@click.argument('stream_id')
@click.option('--timeoffset', '-t', type=int, help='UTC time offset (e.g., -480 for UTC+8)')
@click.option('--start-date', '-s', help='Start date (YYYYMMDD)')
@click.option('--end-date', '-e', help='End date (YYYYMMDD)')
@click.option('--output', '-o', type=click.Choice(['json']), default='json', help='Output format (only json supported)')
@click.pass_context
def stream_state(ctx, project_id, stream_id, timeoffset, start_date, end_date, output):
    """Get the state of the stream
    
    Examples:
        acrcloud bm-cs-projects stream-state 12345 s-ABC123 --timeoffset -480 --start-date 20210301 --end-date 20210302
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_bm_stream_state(
            project_id=project_id,
            stream_id=stream_id,
            timeoffset=timeoffset,
            start_date=start_date,
            end_date=end_date
        )
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_cs_projects.command(name='stream-results')
@click.argument('project_id', type=int)
@click.argument('stream_id')
@click.option('--type', '-t', 'result_type', default='day', type=click.Choice(['last', 'day']), help='Get last or day results')
@click.option('--date', '-d', help='Date (YYYYMMDD)')
@click.option('--min-duration', type=int, help='Min duration seconds')
@click.option('--max-duration', type=int, help='Max duration seconds')
@click.option('--isrc-country', help='ISRC country code')
@click.option('--with-false-positive', type=int, help='Return false positives (0 or 1)')
@click.pass_context
def stream_results(ctx, project_id, stream_id, result_type, date, min_duration, max_duration, isrc_country, with_false_positive):
    """Get stream monitoring results
    
    Examples:
        acrcloud bm-cs-projects stream-results 12345 s-ABC123 --date 20210201
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_bm_stream_results(
            project_id=project_id,
            stream_id=stream_id,
            result_type=result_type,
            date=date,
            min_duration=min_duration,
            max_duration=max_duration,
            isrc_country=isrc_country,
            with_false_positive=with_false_positive
        )
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_cs_projects.command(name='analytics')
@click.argument('project_id', type=int)
@click.option('--stats-type', '-s', required=True, type=click.Choice(['date', 'track', 'artists', 'label', 'stream']), help='Type of data')
@click.option('--result-type', '-r', required=True, type=click.Choice(['music', 'custom']), help='Type of result')
@click.pass_context
def analytics(ctx, project_id, stats_type, result_type):
    """Get analytics data for the last 7 days
    
    Examples:
        acrcloud bm-cs-projects analytics 12345 --stats-type date --result-type music
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_bm_analytics(
            project_id=project_id,
            stats_type=stats_type,
            result_type=result_type
        )
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_cs_projects.command(name='user-report')
@click.argument('project_id', type=int)
@click.argument('stream_id')
@click.option('--data', '-d', required=True, help='JSON string of user result array')
@click.pass_context
def user_report(ctx, project_id, stream_id, data):
    """Insert user results
    
    Examples:
        acrcloud bm-cs-projects user-report 12345 s-ABC123 --data '[{"from":"api","title":"test","timeoffset":0}]'
    """
    api = ctx.obj['api']
    
    try:
        data_list = json.loads(data)
    except json.JSONDecodeError:
        click.echo("Error: --data must be a valid JSON array", err=True)
        return
    
    try:
        result = api.add_bm_stream_user_report(
            project_id=project_id,
            stream_id=stream_id,
            data=data_list
        )
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_cs_projects.command(name='stream-recording')
@click.argument('project_id', type=int)
@click.argument('stream_id')
@click.option('--timestamp-utc', '-t', required=True, help='Start time (YYYYmmddHHMMSS)')
@click.option('--played-duration', '-d', required=True, type=int, help='Duration of recording (seconds)')
@click.option('--record-before', type=int, default=0, help='Seconds of recording to add forward')
@click.option('--record-after', type=int, default=0, help='Seconds of recording to add backwards')
@click.pass_context
def stream_recording(ctx, project_id, stream_id, timestamp_utc, played_duration, record_before, record_after):
    """Get the recording of the results
    
    Examples:
        acrcloud bm-cs-projects stream-recording 12345 s-ABC123 --timestamp-utc 20210607000210 --played-duration 30
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_bm_stream_recording(
            project_id=project_id,
            stream_id=stream_id,
            timestamp_utc=timestamp_utc,
            played_duration=played_duration,
            record_before=record_before,
            record_after=record_after
        )
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
