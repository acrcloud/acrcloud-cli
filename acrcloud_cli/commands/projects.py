"""
Projects command for ACRCloud CLI
"""

import click
import json
from ..api import ACRCloudAPI
from ..utils import output_json, output_table, confirm_action


@click.group(name='projects')
@click.pass_context
def projects(ctx):
    """Manage ACRCloud recognition projects"""
    ctx.obj['api'] = ACRCloudAPI(
        ctx.obj['access_token'],
        ctx.obj['base_url']
    )


@projects.command(name='list')
@click.option('--page', '-p', default=1, help='Page number')
@click.option('--per-page', '-n', default=20, help='Results per page')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list_projects(ctx, page, per_page, output):
    """List all projects
    
    Examples:
        acrcloud projects list
        acrcloud projects list --output json
    """
    api = ctx.obj['api']
    
    try:
        result = api.list_projects(page=page, per_page=per_page)
        
        if output == 'json':
            output_json(result)
        else:
            projects_data = result.get('data', [])
            if not projects_data:
                click.echo("No projects found")
                return
            
            headers = ['ID', 'Name', 'Type', 'Region', 'Audio Type', 'State']
            rows = []
            for project in projects_data:
                rows.append([
                    project.get('id'),
                    project.get('name', '-')[:25],
                    project.get('service_type', '-'),
                    project.get('region', '-'),
                    project.get('audio_type', '-'),
                    'Active' if project.get('state') == 1 else 'Inactive'
                ])
            output_table(headers, rows)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command(name='get')
@click.argument('project_id', type=int)
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def get_project(ctx, project_id, output):
    """Get project details
    
    Examples:
        acrcloud projects get 12345
        acrcloud projects get 12345 --output json
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_project(project_id)
        
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
            click.echo(f"  Type: {project.get('service_type')}")
            click.echo(f"  Region: {project.get('region')}")
            click.echo(f"  Audio Type: {project.get('audio_type')}")
            click.echo(f"  Access Key: {project.get('access_key')}")
            click.echo(f"  Access Secret: {'*' * 20}")
            click.echo(f"  Buckets: {', '.join(map(str, project.get('buckets', [])))}")
            click.echo(f"  State: {'Active' if project.get('state') == 1 else 'Inactive'}")
            click.echo(f"  Created: {project.get('created_at')}")
            click.echo(f"  Updated: {project.get('updated_at')}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command(name='create')
@click.option('--name', '-n', required=True, help='Project name')
@click.option('--type', '-t', 'project_type', required=True,
              type=click.Choice(['AVR', 'LCD', 'HR']),
              help='Project type (AVR=audio/video recognition, LCD=live channel detection, HR=hybrid)')
@click.option('--region', '-r', required=True,
              type=click.Choice(['eu-west-1', 'us-west-2', 'ap-southeast-1']),
              help='Region')
@click.option('--buckets', '-b', default='23', help='Comma-separated bucket IDs')
@click.option('--audio-type', type=click.Choice(['linein', 'recorded']), default='linein',
              help='Audio type (linein=original, recorded=microphone)')
@click.option('--external-ids', '-e', help='External IDs (spotify,deezer,isrc,upc,musicbrainz)')
@click.pass_context
def create_project(ctx, name, project_type, region, buckets, audio_type, external_ids):
    """Create a new recognition project
    
    Examples:
        acrcloud projects create --name my-project --type AVR --region eu-west-1 --buckets "1,2,3"
        acrcloud projects create -n music-detection -t AVR -r ap-southeast-1 -b "12345" --audio-type linein
    """
    api = ctx.obj['api']
    
    bucket_ids = [int(b.strip()) for b in buckets.split(',')]
    
    try:
        result = api.create_project(
            name=name,
            project_type=project_type,
            region=region,
            buckets=bucket_ids,
            audio_type=audio_type,
            external_ids=external_ids
        )
        
        project = result.get('data', {})
        click.echo(f"✓ Project created successfully!")
        click.echo(f"  ID: {project.get('id')}")
        click.echo(f"  Name: {project.get('name')}")
        click.echo(f"  Type: {project.get('service_type')}")
        click.echo(f"  Access Key: {project.get('access_key')}")
        click.echo(f"  Access Secret: {project.get('access_secret')}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command(name='update')
@click.argument('project_id', type=int)
@click.option('--name', '-n', help='New project name')
@click.option('--buckets', '-b', help='Comma-separated bucket IDs')
@click.option('--audio-type', type=click.Choice(['linein', 'recorded']), help='Audio type')
@click.pass_context
def update_project(ctx, project_id, name, buckets, audio_type):
    """Update a project
    
    Examples:
        acrcloud projects update 12345 --name new-name
        acrcloud projects update 12345 -b "1,2,3,4"
    """
    api = ctx.obj['api']
    
    bucket_ids = [int(b.strip()) for b in buckets.split(',')] if buckets else None
    
    try:
        result = api.update_project(
            project_id=project_id,
            name=name,
            buckets=bucket_ids,
            audio_type=audio_type
        )
        
        click.echo(f"✓ Project {project_id} updated successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command(name='delete')
@click.argument('project_id', type=int)
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_project(ctx, project_id, yes):
    """Delete a project
    
    Examples:
        acrcloud projects delete 12345
        acrcloud projects delete 12345 --yes
    """
    api = ctx.obj['api']
    
    if not yes:
        if not confirm_action(f"Are you sure you want to delete project {project_id}?"):
            click.echo("Cancelled")
            return
    
    try:
        api.delete_project(project_id)
        click.echo(f"✓ Project {project_id} deleted successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command(name='bucket-status')
@click.argument('project_id', type=int)
@click.pass_context
def bucket_status(ctx, project_id):
    """Get the status of project's buckets
    
    Examples:
        acrcloud projects bucket-status 12345
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_project_bucket_status(project_id)
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command(name='statistics')
@click.argument('project_id', type=int)
@click.option('--start-date', '-s', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', '-e', help='End date (YYYY-MM-DD)')
@click.pass_context
def project_statistics(ctx, project_id, start_date, end_date):
    """Get project statistics
    
    Examples:
        acrcloud projects statistics 12345
        acrcloud projects statistics 12345 --start-date 2024-01-01 --end-date 2024-12-31
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_project_statistics(
            project_id=project_id,
            start_date=start_date,
            end_date=end_date
        )
        output_json(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
