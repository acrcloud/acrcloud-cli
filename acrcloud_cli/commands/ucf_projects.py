import click
import json
from ..api import ACRCloudAPI
from ..utils import output_json, output_table, confirm_action


@click.group(name='ucf-projects')
@click.pass_context
def ucf_projects(ctx):
    """Manage ACRCloud User Custom Content (UCF) Projects"""
    ctx.obj['api'] = ACRCloudAPI(
        ctx.obj['access_token'],
        ctx.obj['base_url']
    )

# ==================== UCF Projects ====================

@ucf_projects.command(name='list')
@click.option('--region', '-r', help='Filter by region (eu-west-1, us-west-2, ap-southeast-1)')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list_projects(ctx, region, output):
    """List all UCF projects"""
    api = ctx.obj['api']
    
    try:
        response = api.list_ucf_projects(region=region)
        projects = response.get('data', [])
        
        if output == 'json':
            output_json(response)
        else:
            if not projects:
                click.echo("No UCF projects found.")
                return
                
            headers = ['ID', 'Name', 'Region', 'Type', 'Created At']
            rows = []
            
            project_list = projects if isinstance(projects, list) else [projects]
            
            for proj in project_list:
                rows.append([
                    proj.get('id', ''),
                    proj.get('name', ''),
                    proj.get('region', ''),
                    proj.get('type', ''),
                    proj.get('created_at', '')
                ])
                
            output_table(headers, rows)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@ucf_projects.command(name='create')
@click.option('--name', '-n', required=True, help='Project name')
@click.option('--region', '-r', required=True,
              type=click.Choice(['eu-west-1', 'us-west-2', 'ap-southeast-1']),
              help='Region')
@click.option('--type', '-t', 'project_type', default='BM', type=click.Choice(['BM', 'FILES']), help='Project type (BM or FILES)')
@click.option('--config', '-c', help='JSON string config (e.g. {"days":3,"min_ms":5000,"max_ms":300000})')
@click.pass_context
def create_project(ctx, name, region, project_type, config):
    """Create a new UCF project"""
    api = ctx.obj['api']
    
    conf_dict = None
    if config:
        try:
            conf_dict = json.loads(config)
        except json.JSONDecodeError:
            click.echo("Error: --config must be a valid JSON dictionary", err=True)
            return

    try:
        result = api.create_ucf_project(
            name=name,
            region=region,
            project_type=project_type,
            config=conf_dict
        )
        click.echo(f"✓ UCF project '{name}' created successfully!")
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@ucf_projects.command(name='update')
@click.argument('project_id', type=int)
@click.option('--name', '-n', help='Project name')
@click.option('--config', '-c', help='JSON string config')
@click.pass_context
def update_project(ctx, project_id, name, config):
    """Update a UCF project"""
    api = ctx.obj['api']
    
    if not name and not config:
        click.echo("Error: Please specify what to update (--name or --config)", err=True)
        return
        
    conf_dict = None
    if config:
        try:
            conf_dict = json.loads(config)
        except json.JSONDecodeError:
            click.echo("Error: --config must be a valid JSON dictionary", err=True)
            return
            
    try:
        result = api.update_ucf_project(
            project_id=project_id,
            name=name,
            config=conf_dict
        )
        click.echo(f"✓ UCF project {project_id} updated successfully!")
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@ucf_projects.command(name='delete')
@click.argument('project_id', type=int)
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_project(ctx, project_id, yes):
    """Delete a UCF project"""
    api = ctx.obj['api']
    
    if not yes:
        if not confirm_action(f"Are you sure you want to delete UCF project {project_id}?"):
            click.echo("Cancelled")
            return
            
    try:
        api.delete_ucf_project(project_id)
        click.echo(f"✓ UCF project {project_id} deleted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# ==================== UCF BM Streams ====================

@ucf_projects.command(name='list-streams')
@click.argument('project_id', type=int)
@click.option('--page', '-p', default=1, help='Page number')
@click.option('--per-page', default=10, help='Items per page')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list_streams(ctx, project_id, page, per_page, output):
    """List UCF BM streams"""
    api = ctx.obj['api']
    
    try:
        response = api.list_ucf_streams(
            project_id=project_id,
            page=page,
            per_page=per_page
        )
        streams = response.get('data', [])
        
        if output == 'json':
            output_json(response)
        else:
            if not streams:
                click.echo("No BM streams found.")
                return
                
            headers = ['ID', 'BM Stream ID', 'BM Project ID', 'Stream Name', 'Project Name', 'From']
            rows = []
            
            for st in streams:
                rows.append([
                    st.get('id', ''),
                    st.get('bm_stream_id', ''),
                    st.get('bm_project_id', ''),
                    st.get('bm_stream_name', ''),
                    st.get('bm_project_name', ''),
                    st.get('from', '')
                ])
                
            output_table(headers, rows)
            
            if response.get('meta'):
                meta = response['meta']
                click.echo(f"\nPage {meta.get('current_page')} of {meta.get('last_page')} (Total: {meta.get('total', 'Unknown')})")
                
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@ucf_projects.command(name='import-streams')
@click.argument('project_id', type=int)
@click.option('--bm-stream-ids', required=True, help='Comma-separated BM stream IDs')
@click.option('--origin-from', required=True, type=click.Choice(['BM-CUSTOM', 'BM-DATABASE']), help='Source of BM streams')
@click.option('--bm-project-id', required=True, type=int, help='BM project ID')
@click.pass_context
def import_streams(ctx, project_id, bm_stream_ids, origin_from, bm_project_id):
    """Import BM streams to UCF project"""
    api = ctx.obj['api']
    
    try:
        stream_ids_list = [s.strip() for s in bm_stream_ids.split(',') if s.strip()]
        result = api.import_ucf_bm_streams(
            project_id=project_id,
            bm_stream_ids=stream_ids_list,
            origin_from=origin_from,
            bm_project_id=bm_project_id
        )
        click.echo(f"✓ BM streams imported successfully!")
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@ucf_projects.command(name='delete-streams')
@click.argument('project_id', type=int)
@click.option('--stream-ids', '-s', required=True, help='Comma-separated stream IDs')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_streams(ctx, project_id, stream_ids, yes):
    """Delete UCF BM streams"""
    api = ctx.obj['api']
    
    if not yes:
        if not confirm_action(f"Are you sure you want to delete these streams ({stream_ids})?"):
            click.echo("Cancelled")
            return
    
    try:
        api.delete_ucf_bm_streams(project_id=project_id, stream_ids=stream_ids)
        click.echo(f"✓ Streams deleted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# ==================== UCF Results ====================

@ucf_projects.command(name='list-results')
@click.argument('project_id', type=int)
@click.option('--page', '-p', default=1, help='Page number')
@click.option('--per-page', default=10, help='Items per page')
@click.option('--begin-date', help='Begin date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
@click.option('--sortby', type=click.Choice(['id', 'num', 'duration_ms']), help='Sort column')
@click.option('--order', type=click.Choice(['asc', 'desc']), help='Sort order')
@click.option('--status', help='Result status filter (e.g. 0, 2, 6, 10)')
@click.option('--min-duration', help='Min duration (seconds)')
@click.option('--max-duration', help='Max duration (seconds)')
@click.option('--streams', help='Comma-separated stream IDs')
@click.option('--ucf-id', help='UCF item ID filter')
@click.option('--label', help='Label filter (e.g. 0, 1, 2, 3, 4)')
@click.option('--label-value', help='Label value (e.g. advertisement name)')
@click.pass_context
def list_results(ctx, project_id, page, per_page, begin_date, end_date, sortby, order, status,
                 min_duration, max_duration, streams, ucf_id, label, label_value):
    """List UCF results"""
    api = ctx.obj['api']
    
    try:
        result = api.list_ucf_results(
            project_id=project_id, page=page, per_page=per_page,
            begin_date=begin_date, end_date=end_date, sortby=sortby,
            order=order, status=status, min_duration=min_duration,
            max_duration=max_duration, streams=streams, ucf_id=ucf_id,
            label=label, label_value=label_value
        )
        output_json(result)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@ucf_projects.command(name='get-result')
@click.argument('project_id', type=int)
@click.argument('ucf_id', type=str)
@click.pass_context
def get_result(ctx, project_id, ucf_id):
    """Get one UCF item by ID or ACRID"""
    api = ctx.obj['api']
    
    try:
        result = api.get_ucf_result(project_id=project_id, ucf_id=ucf_id)
        output_json(result)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@ucf_projects.command(name='result-details')
@click.argument('project_id', type=int)
@click.argument('ucf_id', type=int)
@click.option('--page', '-p', default=1, help='Page number')
@click.option('--per-page', default=10, help='Items per page')
@click.option('--begin-date', help='Begin date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
@click.pass_context
def result_details(ctx, project_id, ucf_id, page, per_page, begin_date, end_date):
    """Get details of one UCF item"""
    api = ctx.obj['api']
    
    try:
        result = api.get_ucf_result_details(
            project_id=project_id, ucf_id=ucf_id, page=page, per_page=per_page,
            begin_date=begin_date, end_date=end_date
        )
        output_json(result)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@ucf_projects.command(name='record-url')
@click.argument('project_id', type=int)
@click.argument('ucf_id', type=str)
@click.option('--extend', type=int, default=20, help='Seconds to extend at start and end')
@click.pass_context
def record_url(ctx, project_id, ucf_id, extend):
    """Get the UCF audio record URL"""
    api = ctx.obj['api']
    
    try:
        result = api.get_ucf_record_url(project_id=project_id, ucf_id=ucf_id, extend=extend)
        output_json(result)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@ucf_projects.command(name='delete-result')
@click.argument('project_id', type=int)
@click.argument('ucf_id', type=int)
@click.option('--reserved', type=int, default=0, help='0 to delete, 1 to reserve and ignore')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_result(ctx, project_id, ucf_id, reserved, yes):
    """Delete a UCF item or move to reserved queue"""
    api = ctx.obj['api']
    
    action = "reserve" if reserved == 1 else "delete"
    
    if not yes:
        if not confirm_action(f"Are you sure you want to {action} UCF result {ucf_id}?"):
            click.echo("Cancelled")
            return
            
    try:
        api.delete_ucf_item(project_id=project_id, ucf_id=ucf_id, reserved=reserved)
        click.echo(f"✓ UCF result {ucf_id} successfully {action}d!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@ucf_projects.command(name='set-pending')
@click.argument('project_id', type=int)
@click.argument('ucf_id', type=int)
@click.pass_context
def set_pending(ctx, project_id, ucf_id):
    """Make a UCF item status pending"""
    api = ctx.obj['api']
    
    try:
        api.set_ucf_item_pending(project_id=project_id, ucf_id=ucf_id)
        click.echo(f"✓ UCF result {ucf_id} set to pending!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
