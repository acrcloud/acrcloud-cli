"""
File Scanning command for ACRCloud CLI
"""

import click
import json
import os
import time
import struct
from datetime import datetime
from ..api import ACRCloudAPI
from ..utils import output_json, output_table, confirm_action


def _detect_data_type(file_path: str) -> str:
    """Detect data type based on file extension and content.
    
    Returns 'fingerprint' for ACRCloud fingerprint files (.fp), 'audio' otherwise.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    # ACRCloud fingerprint files typically have .fp extension
    if ext == '.fp':
        return 'fingerprint'
    
    # Check if it's a common audio format
    audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.mp4', '.opus'}
    if ext in audio_extensions:
        return 'audio'
    
    # Try to detect by reading file header (magic bytes)
    try:
        with open(file_path, 'rb') as f:
            header = f.read(16)
            # MP3: ID3 tag
            if header[:3] == b'ID3':
                return 'audio'
            # WAV: RIFF...WAVE
            if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
                return 'audio'
            # FLAC: fLaC
            if header[:4] == b'fLaC':
                return 'audio'
            # MP4/M4A: ftyp
            if header[4:8] == b'ftyp':
                return 'audio'
            # OGG: OggS
            if header[:4] == b'OggS':
                return 'audio'
    except Exception:
        pass
    
    # Default to audio
    return 'audio'


def _format_file_info(file_info: dict) -> str:
    """Format file info for table output"""
    state_map = {'0': 'Processing', '1': 'Ready', '-1': 'No results', '-2': 'Error', '-3': 'Error'}
    lines = []
    lines.append(f"  Name: {file_info.get('name', '-')}")
    lines.append(f"  Type: {file_info.get('data_type', '-')}")
    lines.append(f"  Duration: {file_info.get('duration', '-')}s")
    lines.append(f"  URI: {file_info.get('uri', '-')}")
    lines.append(f"  URL: {file_info.get('url', '-')}")
    lines.append(f"  State: {state_map.get(str(file_info.get('state')), file_info.get('state'))}")
    lines.append(f"  Engine: {file_info.get('engine', '-')}")
    lines.append(f"  Created: {file_info.get('created_at', '-')}")
    lines.append(f"  Updated: {file_info.get('updated_at', '-')}")
    return '\n'.join(lines)


def _get_artist_name(artists: list) -> str:
    """Extract artist name from artists array"""
    if not artists:
        return '-'
    artist = artists[0]
    if isinstance(artist, str):
        return artist
    # Handle {name: "X"} or {langs: [{code: "en", name: "X"}]}
    name = artist.get('name')
    if not name and artist.get('langs'):
        name = artist['langs'][0].get('name') if artist['langs'] else None
    return name or '-'


def _get_album_name(album: dict) -> str:
    """Extract album name"""
    if not album:
        return '-'
    return album.get('name', '-') or '-'


def _get_external_ids(result: dict) -> dict:
    """Extract ISRC and UPC from external_ids"""
    ids = result.get('external_ids', {})
    return {
        'isrc': ids.get('isrc', '-'),
        'upc': ids.get('upc', '-'),
    }


def _format_music_match(match: dict, idx: int, title_prefix: str = '') -> list:
    """Format a music match (from music, cover_songs, or custom_files)"""
    lines = []
    result = match.get('result', {})
    title = result.get('title', '-')
    artist = _get_artist_name(result.get('artists', []))
    album = _get_album_name(result.get('album', {}))
    acrid = result.get('acrid', '-')
    audio_id = result.get('audio_id', '-')
    ext_ids = _get_external_ids(result)
    score = result.get('score', '-')
    played_dur = match.get('played_duration', '-')
    offset = match.get('offset', match.get('played_duration', '-'))
    match_type = match.get('type', '-')

    label = f"Match {idx}"
    if title_prefix:
        label = f"{title_prefix} {idx}"
    lines.append(f"    {label}:")
    lines.append(f"      Title: {title}")
    lines.append(f"      Artist: {artist}")
    lines.append(f"      Album: {album}")
    if acrid != '-':
        lines.append(f"      Acrid: {acrid}")
    if audio_id != '-':
        lines.append(f"      Audio ID: {audio_id}")
    if ext_ids['isrc'] != '-':
        lines.append(f"      ISRC: {ext_ids['isrc']}")
    if ext_ids['upc'] != '-':
        lines.append(f"      UPC: {ext_ids['upc']}")
    if score != '-':
        lines.append(f"      Score: {score}")
    lines.append(f"      Type: {match_type}")
    lines.append(f"      Offset: {offset}s")
    if played_dur != '-':
        lines.append(f"      Duration: {played_dur}s")

    # External metadata (spotify, deezer, etc.)
    ext_meta = result.get('external_metadata', {})
    if ext_meta:
        for platform in ['spotify', 'deezer', 'apple', 'youtube', 'musicbrainz']:
            if platform in ext_meta:
                platform_data = ext_meta[platform]
                track_id = platform_data.get('track', {}).get('id', '-')
                if track_id != '-':
                    lines.append(f"      {platform}: {track_id}")

    return lines


def _format_results(results: dict) -> list:
    """Format recognition results dict into a list of display lines"""
    lines = []
    if not results:
        return lines

    # Music recognition results
    if 'music' in results and results['music']:
        lines.append("\n  [Music Recognition]")
        for idx, match in enumerate(results['music'], 1):
            lines.extend(_format_music_match(match, idx))

    # Cover songs results
    if 'cover_songs' in results and results['cover_songs']:
        lines.append("\n  [Cover Songs]")
        for idx, match in enumerate(results['cover_songs'], 1):
            lines.extend(_format_music_match(match, idx, "Cover"))

    # Custom files results
    if 'custom_files' in results and results['custom_files']:
        lines.append("\n  [Custom Files]")
        for idx, match in enumerate(results['custom_files'], 1):
            lines.extend(_format_music_match(match, idx, "File"))

    # Music/Speech detection
    if 'music_speech' in results and results['music_speech']:
        lines.append("\n  [Music/Speech Detection]")
        label_map = {'m': 'Music', 'ms': 'Music & Speech', 's': 'Speech', 'o': 'Others'}
        for idx, seg in enumerate(results['music_speech'], 1):
            label = label_map.get(seg.get('label', ''), seg.get('label', ''))
            lines.append(f"    Segment {idx}: {label} ({seg.get('start', 0)}s - {seg.get('end', 0)}s)")

    # AI detection
    if 'ai_detection' in results and results['ai_detection']:
        lines.append("\n  [AI Detection]")
        for idx, ai in enumerate(results['ai_detection'], 1):
            prediction = ai.get('prediction', '-')
            likely_source = ai.get('likely_source', '-')
            ai_prob = ai.get('ai_probability', '-')
            duration = ai.get('duration', '-')
            lines.append(f"    Detection {idx}:")
            lines.append(f"      Prediction: {prediction}")
            lines.append(f"      Likely Source: {likely_source}")
            lines.append(f"      AI Probability: {ai_prob}%")
            lines.append(f"      Duration: {duration}s")
            # Source probabilities
            source_probs = ai.get('source_probabilities', [])
            if source_probs:
                lines.append(f"      Source Probabilities:")
                for sp in source_probs:
                    lines.append(f"        {sp.get('source', '-')}: {sp.get('probability', '-')}%")

    return lines


def _print_recognition_results(file_info: dict) -> None:
    """Print recognition results in a formatted way"""
    results = file_info.get('results', {})
    result_lines = _format_results(results)

    if result_lines:
        for line in result_lines:
            click.echo(line)
    else:
        click.echo("\n  No matches found.")


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
            
            headers = ['ID', 'Name', 'Region', 'Audio Type', 'Engine', 'Files', 'Size', 'Policy', 'Buckets', 'Created', 'Updated']
            rows = []
            for container in containers:
                rows.append([
                    container.get('id'),
                    container.get('name', '-')[:25],
                    container.get('region', '-'),
                    container.get('audio_type', '-'),
                    container.get('engine', '-'),
                    container.get('num', 0),
                    container.get('size', 0),
                    json.dumps(container.get('policy', {})),
                    ', '.join([str(b.get('name')) for b in container.get('buckets', [])]),
                    container.get('created_at'),
                    container.get('updated_at')
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
            click.echo(f"  Buckets: {', '.join([str(b.get('name')) for b in container.get('buckets', [])])}")
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
@click.option('--buckets', '-b', default='23', help='Bucket IDs (comma-separated or JSON array)')
@click.option('--engine', '-e', required=True, type=click.Choice(['1', '2', '3', '4']),
              help='Engine (1:Audio Fingerprinting, 2:Cover Songs, 3:Both, 4:Speech to Text)')
@click.option('--policy-type', default='traverse', type=click.Choice(['traverse', 'points']),
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
@click.option('--region', '-r', default=None, help='Container region (auto-resolved if not provided)')
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
        acrcloud filescan list-files --container-id 12345
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
@click.option('--region', '-r', default=None, help='Container region (auto-resolved if not provided)')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='json', help='Output format')
@click.pass_context
def get_file(ctx, file_id, container_id, region, output):
    """Get file scanning file details with results
    
    Examples:
        acrcloud filescan get-file FILE_ID --container-id 12345
        acrcloud filescan get-file FILE_ID --container-id 12345 --region eu-west-1
    """
    api = ctx.obj['api']
    
    try:
        result = api.get_fs_file(container_id=container_id, file_id=file_id, region=region)
        
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
            click.echo(_format_file_info(file_info))
            
            # Display recognition results if available
            state = file_info.get('state')
            if state == 1:  # Ready
                click.echo("\nRecognition Results:")
                click.echo("-" * 40)
                _print_recognition_results(file_info)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@filescan.command(name='upload')
@click.option('--container-id', '-c', required=True, type=int, help='Container ID')
@click.option('--region', '-r', default=None, help='Container region (auto-resolved if not provided)')
@click.option('--file', '-f', 'file_path', type=click.Path(exists=True), help='Audio file path')
@click.option('--audio-url', '-u', help='Audio URL')
@click.option('--type', '-t', 'data_type', default=None,
              type=click.Choice(['audio', 'audio_url', 'fingerprint']),
              help='Upload type (auto-detected if not provided)')
@click.pass_context
def upload_file(ctx, container_id, region, file_path, audio_url, data_type):
    """Upload a file to file scanning container
    
    Examples:
        acrcloud filescan upload --container-id 12345 --file audio.mp3
        acrcloud filescan upload -c 12345 -u https://example.com/audio.mp3 -t audio_url
    """
    api = ctx.obj['api']
    
    # Auto-detect data_type if not provided
    if data_type is None:
        if audio_url:
            data_type = 'audio_url'
        elif file_path:
            data_type = _detect_data_type(file_path)
        else:
            data_type = 'audio'
    
    try:
        result = api.upload_fs_file(
            container_id=container_id,
            file_path=file_path,
            audio_url=audio_url,
            data_type=data_type,
            region=region
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
@click.option('--region', '-r', default=None, help='Container region (auto-resolved if not provided)')
@click.option('--file-ids', '-i', required=True, help='Comma-separated file IDs')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_files(ctx, container_id, region, file_ids, yes):
    """Delete files from file scanning container
    
    Examples:
        acrcloud filescan delete-files --container-id 12345 --file-ids "id1,id2"
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
@click.option('--region', '-r', default=None, help='Container region (auto-resolved if not provided)')
@click.option('--file-ids', '-i', required=True, help='Comma-separated file IDs')
@click.pass_context
def rescan_files(ctx, container_id, region, file_ids):
    """Rescan files in file scanning container
    
    Examples:
        acrcloud filescan rescan --container-id 12345 --file-ids "id1,id2"
        acrcloud filescan rescan --container-id 12345 --region eu-west-1 --file-ids "id1,id2"
    """
    api = ctx.obj['api']
    
    try:
        result = api.rescan_fs_files(container_id=container_id, region=region, file_ids=file_ids)
        click.echo(f"✓ Files rescanned successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@filescan.command(name='scan')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--container-id', '-c', type=int, help='Container ID (skip auto-search and use existing container)')
@click.option('--region', '-r', default='eu-west-1',
              type=click.Choice(['eu-west-1', 'us-west-2', 'ap-southeast-1']),
              help='Container region (default: eu-west-1)')
@click.option('--engine', '-e', default='1',
              type=click.Choice(['1', '2', '3', '4']),
              help='Engine (1:Audio Fingerprinting, 2:Cover Songs, 3:Both, 4:Speech to Text, default: 1)')
@click.option('--buckets', '-b', default='23', help='Bucket IDs (comma-separated or JSON array, default: 23)')
@click.option('--policy-type', default='traverse', type=click.Choice(['traverse', 'points']),
              help='Policy type (default: traverse)')
@click.option('--audio-type', default='linein', type=click.Choice(['linein', 'recorded']),
              help='Audio type (default: linein)')
@click.option('--deepright', type=click.Choice(['0', '1']), help='Enable derivative works detection')
@click.option('--music-detection', type=click.Choice(['0', '1']), help='Enable music/speech detection')
@click.option('--ai-detection', type=click.Choice(['0', '1']), help='Enable AI detection')
@click.option('--interval', type=int, default=0, help='Interval for traverse policy (default: 0)')
@click.option('--rec-length', type=int, default=10, help='Recording length for traverse policy (default: 10)')
@click.option('--timeout', type=int, default=600, help='Maximum wait time in seconds for recognition result (default: 600)')
@click.option('--poll-interval', type=int, default=5, help='Polling interval in seconds (default: 5)')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='json', help='Output format')
@click.pass_context
def scan_file(ctx, file_path, container_id, region, engine, buckets, policy_type, audio_type,
              deepright, music_detection, ai_detection, interval, rec_length,
              timeout, poll_interval, output):
    """Scan a file for music recognition
    
    This command will:
    1. Search for existing containers matching the specified parameters (or use --container-id directly)
    2. Create a new container if none exists (when --container-id is not provided)
    3. Upload the file to the container
    4. Poll for recognition results
    
    Examples:
        acrcloud filescan scan audio.mp3
        acrcloud filescan scan audio.mp3 --container-id 12345
        acrcloud filescan scan audio.mp3 --region eu-west-1 --engine 1 --buckets "23,24"
        acrcloud filescan scan fingerprint.fp --container-id 12345 --poll-interval 5
    """
    api = ctx.obj['api']
    
    # Parse buckets
    try:
        buckets_list = json.loads(buckets) if buckets.startswith('[') else [int(b.strip()) for b in buckets.split(',')]
    except:
        buckets_list = [int(buckets)] if buckets.isdigit() else [23]
    
    # Convert engine to int
    engine_int = int(engine)
    
    # Convert optional flags to bool
    deepright_bool = deepright == '1' if deepright else None
    music_detection_bool = music_detection == '1' if music_detection else None
    ai_detection_bool = ai_detection == '1' if ai_detection else None
    
    container = None
    resolved_container_id = None
    
    try:
        # Step 1: Use provided container-id or search for existing containers
        if container_id:
            resolved_container_id = container_id
            click.echo(f"Using specified container: ID={container_id}")
        else:
            click.echo("Searching for existing containers...")
            result = api.list_fs_containers(page=1, per_page=100, region=region)
            containers = result.get('data', [])
            
            # Filter containers by parameters
            matching_containers = []
            for c in containers:
                # Check region match
                if c.get('region') != region:
                    continue
                
                # Check engine match
                if c.get('engine') != engine_int:
                    continue
                
                # Check audio_type match
                if c.get('audio_type') != audio_type:
                    continue
                
                # Check buckets match (allow subset)
                container_buckets = [b.get('id') for b in c.get('buckets', [])]
                if set(buckets_list) != set(container_buckets):
                    continue
                
                # Check policy type match
                container_policy = c.get('policy', {})
                if container_policy.get('type') != policy_type:
                    continue
                
                # Check deepright match (if specified)
                if deepright_bool is not None and c.get('deepright') != deepright_bool:
                    continue
                
                # Check music_detection match (if specified)
                if music_detection_bool is not None and c.get('music_detection') != music_detection_bool:
                    continue
                
                # Check ai_detection match (if specified)
                if ai_detection_bool is not None and c.get('ai_detection') != ai_detection_bool:
                    continue
                
                matching_containers.append(c)
            
            if matching_containers:
                # Sort by created_at to get the most recently created
                matching_containers.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                container = matching_containers[0]
                resolved_container_id = container.get('id')
                click.echo(f"✓ Found existing container: ID={resolved_container_id}, Name={container.get('name')}")
            else:
                click.echo("No matching container found, creating new container...")
                
                # Step 2: Create new container with default/auto-generated name
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                container_name = f"scan_container_{timestamp}"
            
            # Build policy
            policy = {'type': policy_type}
            if policy_type == 'traverse':
                policy['interval'] = interval
                policy['rec_length'] = rec_length
            
            result = api.create_fs_container(
                name=container_name,
                region=region,
                audio_type=audio_type,
                buckets=buckets_list,
                engine=engine_int,
                policy=policy,
                deepright=deepright_bool,
                music_detection=music_detection_bool,
                ai_detection=ai_detection_bool
            )
            
            container = result.get('data', {})
            resolved_container_id = container.get('id')
            click.echo(f"✓ Created new container: ID={resolved_container_id}, Name={container_name}")
        
        # Step 3: Upload file
        click.echo(f"Uploading file: {file_path}...")
        file_basename = os.path.basename(file_path)
        detected_type = _detect_data_type(file_path)
        upload_result = api.upload_fs_file(
            container_id=resolved_container_id,
            region=region,
            file_path=file_path,
            data_type=detected_type,
            name=file_basename
        )
        
        file_data = upload_result.get('data', {})
        if isinstance(file_data, dict):
            file_id = file_data.get('id')
            file_name = file_data.get('name', file_path)
        else:
            file_id = None
            file_name = file_path
        
        click.echo(f"✓ File uploaded successfully!")
        if file_id:
            click.echo(f"  File ID: {file_id}")
        
        # Step 4: Poll for results
        click.echo(f"Waiting for recognition results (timeout: {timeout}s, poll interval: {poll_interval}s)...")
        
        # Wait initial poll_interval before first check
        time.sleep(poll_interval)
        
        start_time = time.time()
        final_result = None
        
        while time.time() - start_time < timeout:
            # Get file status
            file_result = api.get_fs_file(container_id=resolved_container_id, region=region, file_id=file_id or file_name)
            file_info_list = file_result.get('data', [])
            
            if not file_info_list:
                click.echo("  Waiting for processing...")
                time.sleep(poll_interval)
                continue
            
            # Handle both single file and array response
            if isinstance(file_info_list, list) and len(file_info_list) > 0:
                file_info = file_info_list[0]
            else:
                file_info = file_info_list
            
            state = file_info.get('state')
            state_map = {'0': 'Processing', '1': 'Ready', '-1': 'No results', '-2': 'Error', '-3': 'Error'}
            state_str = state_map.get(str(state), f'Unknown({state})')
            
            click.echo(f"  Status: {state_str}")
            
            # Check if processing is complete
            if state == 1:  # Ready
                final_result = file_result
                click.echo("✓ Recognition completed!")
                break
            elif state in [-1, -2, -3]:  # No results or Error
                final_result = file_result
                click.echo(f"✓ Recognition finished with status: {state_str}")
                break
            
            time.sleep(poll_interval)
        
        if final_result is None:
            click.echo(f"⚠ Timeout reached after {timeout}s. The file is still being processed.")
            click.echo(f"  You can check the result later using:")
            click.echo(f"    acrcloud filescan get-file {file_id or file_name} --container-id {resolved_container_id} --region {region}")
            return
        
        # Output final result
        if output == 'json':
            output_json(final_result)
        else:
            file_data = final_result.get('data', [])
            if isinstance(file_data, list) and len(file_data) > 0:
                file_info = file_data[0]
            else:
                file_info = file_data
            
            click.echo("\nRecognition Result:")
            click.echo("-" * 40)
            click.echo(_format_file_info(file_info))
            _print_recognition_results(file_info)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
