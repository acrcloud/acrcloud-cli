import click
import json
from ..api import ACRCloudAPI
from ..utils import output_json, output_table, confirm_action


@click.group(name='bm-bd-projects')
@click.pass_context
def bm_bd_projects(ctx):
    """Manage ACRCloud BM (Broadcast Monitoring) Database Projects"""
    ctx.obj['api'] = ACRCloudAPI(
        ctx.obj['access_token'],
        ctx.obj['base_url']
    )

# ==================== BM Database Projects ====================

@bm_bd_projects.command(name='list')
@click.option('--region', '-r', help='Filter by region (eu-west-1, us-west-2, ap-southeast-1)')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list_projects(ctx, region, output):
    """List all BM Database projects
    
    Examples:
        acrcloud bm-bd-projects list
        acrcloud bm-bd-projects list --region eu-west-1
    """
    api = ctx.obj['api']
    
    try:
        response = api.list_bm_bd_projects(region=region)
        projects = response.get('data', [])
        
        if output == 'json':
            output_json(response)
        else:
            if not projects:
                click.echo("No BM database projects found.")
                return
                
            headers = ['ID', 'Name', 'Region', 'Status Check', 'Created At']
            rows = []
            
            # The list API returns array directly in data normally
            project_list = projects if isinstance(projects, list) else [projects]
            
            for proj in project_list:
                rows.append([
                    proj.get('id', ''),
                    proj.get('name', ''),
                    proj.get('region', ''),
                    proj.get('status_check', ''),
                    proj.get('created_at', '')
                ])
                
            output_table(headers, rows)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_bd_projects.command(name='create')
@click.option('--name', '-n', required=True, help='Project name')
@click.option('--region', '-r', required=True,
              type=click.Choice(['eu-west-1', 'us-west-2', 'ap-southeast-1']),
              help='Region')
@click.option('--buckets', '-b', required=True, help='Bucket IDs (comma-separated)')
@click.pass_context
def create_project(ctx, name, region, buckets):
    """Create a new BM Database project
    
    Examples:
        acrcloud bm-bd-projects create --name my-db-project --region eu-west-1 --buckets "14661"
    """
    api = ctx.obj['api']
    
    try:
        bucket_ids = [int(b.strip()) for b in buckets.split(',') if b.strip()]
        result = api.create_bm_bd_project(
            name=name,
            region=region,
            buckets=bucket_ids
        )
        click.echo(f"✓ BM Database project '{name}' created successfully!")
        output_json(result)
        
    except ValueError:
        click.echo("Error: Invalid bucket IDs format. Must be comma-separated integers.", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_bd_projects.command(name='update')
@click.argument('project_id', type=int)
@click.option('--name', '-n', help='Project name')
@click.option('--buckets', '-b', help='Bucket IDs (comma-separated)')
@click.pass_context
def update_project(ctx, project_id, name, buckets):
    """Update a BM Database project
    
    Examples:
        acrcloud bm-bd-projects update 12345 --name new-name
    """
    api = ctx.obj['api']
    
    if not name and not buckets:
        click.echo("Error: Please specify what to update (--name or --buckets)", err=True)
        return
        
    try:
        bucket_ids = None
        if buckets:
            bucket_ids = [int(b.strip()) for b in buckets.split(',') if b.strip()]
            
        result = api.update_bm_bd_project(
            project_id=project_id,
            name=name,
            buckets=bucket_ids
        )
        click.echo(f"✓ BM Database project {project_id} updated successfully!")
        output_json(result)
        
    except ValueError:
        click.echo("Error: Invalid bucket IDs format. Must be comma-separated integers.", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_bd_projects.command(name='delete')
@click.argument('project_id', type=int)
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_project(ctx, project_id, yes):
    """Delete a BM Database project
    
    Examples:
        acrcloud bm-bd-projects delete 12345
    """
    api = ctx.obj['api']
    
    if not yes:
        if not confirm_action(f"Are you sure you want to delete BM Database project {project_id}?"):
            click.echo("Cancelled")
            return
            
    try:
        api.delete_bm_bd_project(project_id)
        click.echo(f"✓ BM Database project {project_id} deleted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_bd_projects.command(name='set-callback')
@click.argument('project_id', type=int)
@click.option('--url', '-u', required=True, help='Callback URL')
@click.option('--send-noresult', type=int, default=0, help='Inform when no content detected (0 or 1)')
@click.option('--result-type', type=int, default=0, help='Callback result type (0: RealTime, 1: Delay)')
@click.pass_context
def set_callback(ctx, project_id, url, send_noresult, result_type):
    """Set result callback URL for BM Database project
    
    Examples:
        acrcloud bm-bd-projects set-callback 12345 --url https://callback.example.com/results
    """
    api = ctx.obj['api']
    
    try:
        api.set_bm_bd_result_callback(
            project_id=project_id,
            result_callback_url=url,
            result_callback_send_noresult=send_noresult,
            result_callback_result_type=result_type
        )
        click.echo(f"✓ Callback URL set successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_bd_projects.command(name='set-state-callback')
@click.argument('project_id', type=int)
@click.option('--url', '-u', required=True, help='State notification URL')
@click.pass_context
def set_state_callback(ctx, project_id, url):
    """Set state notification callback for BM Database project
    
    Examples:
        acrcloud bm-bd-projects set-state-callback 12345 --url https://callback.example.com/state
    """
    api = ctx.obj['api']
    
    try:
        api.set_bm_bd_state_notification_callback(
            project_id=project_id,
            state_callback_url=url
        )
        click.echo(f"✓ State notification callback set successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# ==================== BM Database Channels ====================

@bm_bd_projects.command(name='list-channels')
@click.argument('project_id', type=int)
@click.option('--page', '-p', default=1, help='Page number')
@click.option('--state', '-s', default='All', type=click.Choice(['All', 'Running', 'Timeout', 'Paused', 'Invalid URL', 'Mute', 'Other']), help='Filter by state')
@click.option('--timemap', type=click.Choice(['0', '1']), help='Filter by timemap')
@click.option('--search-type', type=click.Choice(['channel_id', 'channel_name', 'city', 'custom_id', 'mytuner_id']), help='Search field')
@click.option('--search-value', help='Search value')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list_channels(ctx, project_id, page, state, timemap, search_type, search_value, output):
    """List channels in BM Database project
    
    Examples:
        acrcloud bm-bd-projects list-channels 12345
        acrcloud bm-bd-projects list-channels 12345 --state Running
    """
    api = ctx.obj['api']
    
    if search_type and not search_value:
        click.echo("Error: --search-value is required when using --search-type", err=True)
        return
        
    try:
        response = api.list_bm_bd_channels(
            project_id=project_id,
            state=state,
            timemap=timemap,
            search_type=search_type,
            search_value=search_value,
            page=page
        )
        channels = response.get('data', [])
        
        if output == 'json':
            output_json(response)
        else:
            if not channels:
                click.echo("No channels found.")
                return
                
            headers = ['ID', 'Name', 'Status Code', 'Language', 'Country']
            rows = []
            
            for ch in channels:
                rows.append([
                    ch.get('id', ''),
                    ch.get('name', ''),
                    ch.get('status_code', ''),
                    ch.get('language', ''),
                    ch.get('country', '')
                ])
                
            output_table(headers, rows)
            
            if response.get('meta'):
                meta = response['meta']
                click.echo(f"\nPage {meta.get('current_page')} of {meta.get('last_page')} (Total: {meta.get('total', 'Unknown')})")
                
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_bd_projects.command(name='add-channels')
@click.argument('project_id', type=int)
@click.option('--channels', '-c', required=True, help='Comma-separated channel IDs')
@click.pass_context
def add_channels(ctx, project_id, channels):
    """Add channels to BM Database project
    
    Examples:
        acrcloud bm-bd-projects add-channels 12345 --channels "238766,238767"
    """
    api = ctx.obj['api']
    
    try:
        channel_ids = [int(c.strip()) for c in channels.split(',') if c.strip()]
        result = api.add_bm_bd_channels(project_id=project_id, channels=channel_ids)
        click.echo(f"✓ Channels added successfully!")
        output_json(result)
        
    except ValueError:
        click.echo("Error: Invalid channel IDs format. Must be comma-separated integers.", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_bd_projects.command(name='delete-channels')
@click.argument('project_id', type=int)
@click.option('--channel-ids', '-c', required=True, help='Comma-separated channel IDs')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_channels(ctx, project_id, channel_ids, yes):
    """Delete channels from BM Database project
    
    Examples:
        acrcloud bm-bd-projects delete-channels 12345 --channel-ids "238766"
    """
    api = ctx.obj['api']
    
    if not yes:
        if not confirm_action(f"Are you sure you want to delete these channels?"):
            click.echo("Cancelled")
            return
    
    try:
        api.delete_bm_bd_channels(project_id=project_id, channel_ids=channel_ids)
        click.echo(f"✓ Channels deleted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_bd_projects.command(name='set-custom-id')
@click.argument('project_id', type=int)
@click.argument('channel_id', type=int)
@click.option('--custom-id', '-c', required=True, help='Custom ID to set')
@click.pass_context
def set_custom_id(ctx, project_id, channel_id, custom_id):
    """Set custom_id for a channel
    
    Examples:
        acrcloud bm-bd-projects set-custom-id 12345 238766 --custom-id "MyID_1"
    """
    api = ctx.obj['api']
    
    try:
        result = api.set_bm_bd_channel_custom_id(project_id=project_id, channel_id=channel_id, custom_id=custom_id)
        click.echo(f"✓ Custom ID set successfully!")
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# ==================== BM Database Channels Data ====================

@bm_bd_projects.command(name='channel-state')
@click.argument('project_id', type=int)
@click.argument('channel_id', type=int)
@click.option('--timeoffset', '-t', type=int, help='UTC time offset (e.g., 0)')
@click.option('--start-date', '-s', help='Start date (YYYYMMDD)')
@click.option('--end-date', '-e', help='End date (YYYYMMDD)')
@click.option('--output', '-o', type=click.Choice(['json']), default='json', help='Output format (only json supported)')
@click.pass_context
def channel_state(ctx, project_id, channel_id, timeoffset, start_date, end_date, output):
    """Get the state of the channel
    
    Examples:
        acrcloud bm-bd-projects channel-state 1234 295704 --timeoffset 0 --start-date 20210301 --end-date 20210302
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_bm_bd_channel_state(
            project_id=project_id,
            channel_id=channel_id,
            timeoffset=timeoffset,
            start_date=start_date,
            end_date=end_date
        )
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_bd_projects.command(name='channel-results')
@click.argument('project_id', type=int)
@click.argument('channel_id', type=int)
@click.option('--type', '-t', 'result_type', default='day', type=click.Choice(['last', 'day']), help='Get last or day results')
@click.option('--date', '-d', help='Date (YYYYMMDD)')
@click.option('--min-duration', type=int, help='Min duration seconds')
@click.option('--max-duration', type=int, help='Max duration seconds')
@click.option('--isrc-country', help='ISRC country code')
@click.option('--with-false-positive', type=int, help='Return false positives (0 or 1)')
@click.pass_context
def channel_results(ctx, project_id, channel_id, result_type, date, min_duration, max_duration, isrc_country, with_false_positive):
    """Get non-real-time results of channel monitoring
    
    Examples:
        acrcloud bm-bd-projects channel-results 12345 100251 --date 20210107
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_bm_bd_channel_results(
            project_id=project_id,
            channel_id=channel_id,
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


@bm_bd_projects.command(name='unknown-results')
@click.argument('project_id', type=int)
@click.argument('channel_id', type=int)
@click.option('--date', '-d', required=True, help='Date (YYYYMMDD)')
@click.option('--min-duration', type=int, help='Min duration seconds')
@click.option('--max-duration', type=int, help='Max duration seconds')
@click.pass_context
def unknown_results(ctx, project_id, channel_id, date, min_duration, max_duration):
    """Get unknown music results of channel monitoring
    
    Examples:
        acrcloud bm-bd-projects unknown-results 12345 100251 --date 20210107
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_bm_bd_channel_unknown_results(
            project_id=project_id,
            channel_id=channel_id,
            date=date,
            min_duration=min_duration,
            max_duration=max_duration
        )
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_bd_projects.command(name='realtime-results')
@click.argument('project_id', type=int)
@click.argument('channel_id', type=int)
@click.pass_context
def realtime_results(ctx, project_id, channel_id):
    """Get real-time results of channel monitoring
    
    Examples:
        acrcloud bm-bd-projects realtime-results 12345 100251
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_bm_bd_channel_realtime_results(
            project_id=project_id,
            channel_id=channel_id
        )
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_bd_projects.command(name='analytics')
@click.argument('project_id', type=int)
@click.option('--stats-type', '-s', required=True, type=click.Choice(['date', 'track', 'artists', 'label', 'channel']), help='Type of data')
@click.option('--result-type', '-r', required=True, type=click.Choice(['music', 'custom']), help='Type of result')
@click.pass_context
def analytics(ctx, project_id, stats_type, result_type):
    """Get analytics data for the last 7 days
    
    Examples:
        acrcloud bm-bd-projects analytics 1234 --stats-type date --result-type music
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_bm_bd_analytics(
            project_id=project_id,
            stats_type=stats_type,
            result_type=result_type
        )
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_bd_projects.command(name='user-report')
@click.argument('project_id', type=int)
@click.argument('channel_id', type=int)
@click.option('--data', '-d', required=True, help='JSON string of user result array')
@click.pass_context
def user_report(ctx, project_id, channel_id, data):
    """Insert user results
    
    Examples:
        acrcloud bm-bd-projects user-report 179 100251 --data '[{"from":"api","title":"test","timeoffset":0}]'
    """
    api = ctx.obj['api']
    
    try:
        data_list = json.loads(data)
    except json.JSONDecodeError:
        click.echo("Error: --data must be a valid JSON array", err=True)
        return
    
    try:
        result = api.add_bm_bd_channel_user_report(
            project_id=project_id,
            channel_id=channel_id,
            data=data_list
        )
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@bm_bd_projects.command(name='channel-recording')
@click.argument('project_id', type=int)
@click.argument('channel_id', type=int)
@click.option('--timestamp-utc', '-t', required=True, help='Start time (YYYYmmddHHMMSS)')
@click.option('--played-duration', '-d', required=True, type=int, help='Duration of recording (seconds)')
@click.option('--record-before', type=int, default=0, help='Seconds of recording to add forward')
@click.option('--record-after', type=int, default=0, help='Seconds of recording to add backwards')
@click.pass_context
def channel_recording(ctx, project_id, channel_id, timestamp_utc, played_duration, record_before, record_after):
    """Get the recording of the results
    
    Examples:
        acrcloud bm-bd-projects channel-recording 100079 100123 -t 20210601121314 -d 30
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_bm_bd_channel_recording(
            project_id=project_id,
            channel_id=channel_id,
            timestamp_utc=timestamp_utc,
            played_duration=played_duration,
            record_before=record_before,
            record_after=record_after
        )
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
