"""
ACRCloud API Client
"""

import requests
import json
import os
from typing import Optional, Dict, Any, List


class ACRCloudAPI:
    """ACRCloud Console API Client"""
    
    def __init__(self, access_token: str, base_url: str = 'https://api-v2.acrcloud.com/api'):
        self.access_token = access_token
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def _request(self, method: str, endpoint: str, base_url: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{base_url if base_url else self.base_url}{endpoint}"
        
        headers = kwargs.get('headers', {})
        
        # Handle files separately for multipart/form-data
        if 'files' in kwargs:
            # Explicitly suppress session's Content-Type for multipart
            if 'Content-Type' not in headers:
                headers['Content-Type'] = None
            response = self.session.request(method, url, headers=headers, **kwargs)
        else:
            response = self.session.request(method, url, **kwargs)
        
        try:
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error {response.status_code}"
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_msg = f"{error_msg}: {error_data['message']}"
                elif 'error' in error_data:
                    error_msg = f"{error_msg}: {error_data['error']}"
            except:
                error_msg = f"{error_msg}: {response.text}"
            raise APIError(error_msg, response.status_code)
        except json.JSONDecodeError:
            return {'raw_response': response.text}
    
    # ==================== Buckets ====================
    
    def list_buckets(self, page: int = 1, per_page: int = 20, 
                     region: Optional[str] = None, 
                     bucket_type: Optional[str] = None) -> Dict:
        """List all buckets"""
        params = {'page': page, 'per_page': per_page}
        if region:
            params['region'] = region
        if bucket_type:
            params['type'] = bucket_type
        return self._request('GET', '/buckets', params=params)
    
    def get_bucket(self, bucket_id: int) -> Dict:
        """Get a specific bucket"""
        return self._request('GET', f'/buckets/{bucket_id}')
    
    def create_bucket(self, name: str, bucket_type: str, region: str,
                      net_type: int = 1, labels: Optional[List[str]] = None,
                      metadata_template: Optional[str] = None) -> Dict:
        """Create a new bucket"""
        data = {
            'name': name,
            'type': bucket_type,
            'region': region,
            'net_type': net_type
        }
        if labels:
            data['labels'] = labels
        if metadata_template:
            data['metadata_template'] = metadata_template
        return self._request('POST', '/buckets', json=data)
    
    def update_bucket(self, bucket_id: int, name: Optional[str] = None,
                      labels: Optional[List[str]] = None,
                      metadata_template: Optional[str] = None) -> Dict:
        """Update a bucket"""
        data = {}
        if name:
            data['name'] = name
        if labels:
            data['labels'] = labels
        if metadata_template:
            data['metadata_template'] = metadata_template
        return self._request('PUT', f'/buckets/{bucket_id}', json=data)
    
    def delete_bucket(self, bucket_id: int) -> Dict:
        """Delete a bucket"""
        return self._request('DELETE', f'/buckets/{bucket_id}')
    
    # ==================== Audio Files ====================
    
    def list_files(self, bucket_id: int, page: int = 1, 
                   per_page: int = 20, keyword: Optional[str] = None) -> Dict:
        """List files in a bucket"""
        params = {'page': page, 'per_page': per_page}
        if keyword:
            params['keyword'] = keyword
        return self._request('GET', f'/buckets/{bucket_id}/files', params=params)
    
    def get_file(self, bucket_id: int, file_id: int) -> Dict:
        """Get a specific file"""
        return self._request('GET', f'/buckets/{bucket_id}/files/{file_id}')
    
    def upload_file(self, bucket_id: int, file_path: Optional[str] = None,
                    title: Optional[str] = None, data_type: str = 'audio',
                    audio_url: Optional[str] = None, acrid: Optional[str] = None,
                    user_defined: Optional[Dict] = None) -> Dict:
        """Upload an audio file or fingerprint to a bucket"""
        data = {'data_type': data_type}
        
        if title:
            data['title'] = title
        if user_defined:
            data['user_defined'] = json.dumps(user_defined)
        
        files = None
        
        if data_type == 'audio' and file_path:
            files = {'file': open(file_path, 'rb')}
        elif data_type == 'fingerprint' and file_path:
            files = {'file': open(file_path, 'rb')}
        elif data_type == 'audio_url' and audio_url:
            data['url'] = audio_url
        elif data_type == 'acrid' and acrid:
            data['acrid'] = acrid
        
        try:
            if files:
                return self._request('POST', f'/buckets/{bucket_id}/files', data=data, files=files)
            else:
                return self._request('POST', f'/buckets/{bucket_id}/files', json=data)
        finally:
            if files:
                for f in files.values():
                    f.close()
    
    def update_file(self, bucket_id: int, file_id: int, 
                    title: Optional[str] = None,
                    user_defined: Optional[Dict] = None) -> Dict:
        """Update a file"""
        data = {}
        if title:
            data['title'] = title
        if user_defined:
            data['user_defined'] = json.dumps(user_defined)
        return self._request('PUT', f'/buckets/{bucket_id}/files/{file_id}', json=data)
    
    def delete_file(self, bucket_id: int, file_id: int) -> Dict:
        """Delete a file"""
        return self._request('DELETE', f'/buckets/{bucket_id}/files/{file_id}')
    
    def delete_files_batch(self, bucket_id: int, file_ids: List[int]) -> Dict:
        """Delete multiple files"""
        return self._request('DELETE', f'/buckets/{bucket_id}/files', json={'ids': file_ids})
    
    def move_files(self, bucket_id: int, target_bucket_id: int, 
                   file_ids: List[int]) -> Dict:
        """Move files to another bucket"""
        data = {
            'target_bucket_id': target_bucket_id,
            'ids': file_ids
        }
        return self._request('POST', f'/buckets/{bucket_id}/files/move', json=data)
    
    def dump_files(self, bucket_id: int) -> Dict:
        """Dump all files information in a bucket (once per day limit)"""
        return self._request('GET', f'/buckets/{bucket_id}/files/dump')
    
    # ==================== Live Channels ====================
    
    def list_channels(self, bucket_id: int, page: int = 1, 
                      per_page: int = 20) -> Dict:
        """List live channels in a bucket"""
        params = {'page': page, 'per_page': per_page}
        return self._request('GET', f'/buckets/{bucket_id}/channels', params=params)
    
    def get_channel(self, bucket_id: int, channel_id: int) -> Dict:
        """Get a specific channel"""
        return self._request('GET', f'/buckets/{bucket_id}/channels/{channel_id}')
    
    def create_channel(self, bucket_id: int, name: str, url: str,
                       record: Optional[int] = None, 
                       timeshift: Optional[int] = None,
                       user_defined: Optional[Dict] = None) -> Dict:
        """Create a live channel"""
        data = {'name': name, 'url': url}
        if record is not None:
            data['record'] = record
        if timeshift is not None:
            data['timeshift'] = timeshift
        if user_defined:
            data['user_defined'] = user_defined
        return self._request('POST', f'/buckets/{bucket_id}/channels', json=data)
    
    def update_channel(self, bucket_id: int, channel_id: int,
                       name: Optional[str] = None, url: Optional[str] = None,
                       record: Optional[int] = None,
                       timeshift: Optional[int] = None) -> Dict:
        """Update a channel"""
        data = {}
        if name:
            data['name'] = name
        if url:
            data['url'] = url
        if record is not None:
            data['record'] = record
        if timeshift is not None:
            data['timeshift'] = timeshift
        return self._request('PUT', f'/buckets/{bucket_id}/channels/{channel_id}', json=data)
    
    def delete_channel(self, bucket_id: int, channel_id: int) -> Dict:
        """Delete a channel"""
        return self._request('DELETE', f'/buckets/{bucket_id}/channels/{channel_id}')
    
    # ==================== Base Projects ====================
    
    def list_projects(self, page: int = 1, per_page: int = 20) -> Dict:
        """List all base projects"""
        params = {'page': page, 'per_page': per_page}
        return self._request('GET', '/base-projects', params=params)
    
    def get_project(self, project_id: int) -> Dict:
        """Get a specific project"""
        return self._request('GET', f'/base-projects/{project_id}')
    
    def create_project(self, name: str, project_type: str, region: str,
                       buckets: List[int], audio_type: str = 'linein',
                       external_ids: Optional[str] = None) -> Dict:
        """Create a new recognition project"""
        data = {
            'name': name,
            'type': project_type,
            'region': region,
            'buckets': buckets,
            'audio_type': audio_type
        }
        if external_ids:
            data['external_ids'] = external_ids
        return self._request('POST', '/base-projects', json=data)
    
    def update_project(self, project_id: int, name: Optional[str] = None,
                       buckets: Optional[List[int]] = None,
                       audio_type: Optional[str] = None) -> Dict:
        """Update a project"""
        data = {}
        if name:
            data['name'] = name
        if buckets:
            data['buckets'] = buckets
        if audio_type:
            data['audio_type'] = audio_type
        return self._request('PUT', f'/base-projects/{project_id}', json=data)
    
    def delete_project(self, project_id: int) -> Dict:
        """Delete a project"""
        return self._request('DELETE', f'/base-projects/{project_id}')
    
    def get_project_bucket_status(self, project_id: int) -> Dict:
        """Get the status of project's buckets"""
        return self._request('GET', f'/base-projects/{project_id}/bucket-status')
    
    def get_project_statistics(self, project_id: int, 
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> Dict:
        """Get project statistics"""
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self._request('GET', f'/base-projects/{project_id}/statistics', params=params)
    
    # ==================== File Scanning (FS Containers) ====================
    
    def list_fs_containers(self, page: int = 1, per_page: int = 20,
                           region: Optional[str] = None,
                           name: Optional[str] = None) -> Dict:
        """List all file scanning containers"""
        params = {'page': page, 'per_page': per_page}
        if region:
            params['region'] = region
        if name:
            params['name'] = name
        return self._request('GET', '/fs-containers', params=params)
    
    def get_fs_container(self, container_id: int) -> Dict:
        """Get a specific file scanning container"""
        return self._request('GET', f'/fs-containers/{container_id}')
    
    def create_fs_container(self, name: str, region: str, audio_type: str,
                            buckets: List, engine: int, policy: Dict,
                            callback_url: Optional[str] = None,
                            deepright: Optional[bool] = None,
                            music_detection: Optional[bool] = None,
                            ai_detection: Optional[bool] = None) -> Dict:
        """Create a new file scanning container"""
        data = {
            'name': name,
            'region': region,
            'audio_type': audio_type,
            'buckets': buckets,
            'engine': engine,
            'policy': policy
        }
        if callback_url:
            data['callback_url'] = callback_url
        if deepright is not None:
            data['deepright'] = deepright
        if music_detection is not None:
            data['music_detection'] = music_detection
        if ai_detection is not None:
            data['ai_detection'] = ai_detection
        return self._request('POST', '/fs-containers', json=data)
    
    def update_fs_container(self, container_id: int, name: Optional[str] = None,
                            audio_type: Optional[str] = None,
                            buckets: Optional[List] = None,
                            engine: Optional[int] = None,
                            policy: Optional[Dict] = None,
                            callback_url: Optional[str] = None,
                            deepright: Optional[bool] = None,
                            music_detection: Optional[bool] = None,
                            ai_detection: Optional[bool] = None) -> Dict:
        """Update a file scanning container"""
        data = {}
        if name:
            data['name'] = name
        if audio_type:
            data['audio_type'] = audio_type
        if buckets:
            data['buckets'] = buckets
        if engine is not None:
            data['engine'] = engine
        if policy:
            data['policy'] = policy
        if callback_url:
            data['callback_url'] = callback_url
        if deepright is not None:
            data['deepright'] = deepright
        if music_detection is not None:
            data['music_detection'] = music_detection
        if ai_detection is not None:
            data['ai_detection'] = ai_detection
        return self._request('PUT', f'/fs-containers/{container_id}', json=data)
    
    def delete_fs_container(self, container_id: int) -> Dict:
        """Delete a file scanning container"""
        return self._request('DELETE', f'/fs-containers/{container_id}')
    
    # ==================== File Scanning (FsFiles) ====================
    
    def _get_fs_base_url(self, region: str) -> str:
        """Get region-specific base URL for file scanning"""
        return f'https://api-{region}.acrcloud.com/api'
    
    def list_fs_files(self, container_id: int, region: str, page: int = 1,
                      per_page: int = 20, search: Optional[str] = None,
                      with_result: Optional[int] = None,
                      state: Optional[str] = None) -> Dict:
        """List files in a file scanning container"""
        base_url = self._get_fs_base_url(region)
        params = {'page': page, 'per_page': per_page}
        if search:
            params['search'] = search
        if with_result is not None:
            params['with_result'] = with_result
        if state:
            params['state'] = state
        
        return self._request('GET', f'/fs-containers/{container_id}/files', 
                            base_url=self._get_fs_base_url(region), params=params)
    
    def get_fs_file(self, container_id: int, region: str, file_id: str) -> Dict:
        """Get a specific file scanning file"""
        return self._request('GET', f'/fs-containers/{container_id}/files/{file_id}',
                            base_url=self._get_fs_base_url(region))
    
    def upload_fs_file(self, container_id: int, region: str,
                       file_path: Optional[str] = None,
                       audio_url: Optional[str] = None,
                       data_type: str = 'audio',
                       name: Optional[str] = None) -> Dict:
        """Upload a file to file scanning container"""
        base_url = self._get_fs_base_url(region)
        data = {'data_type': data_type}
        if name:
            data['name'] = name
            
        files = None
        if data_type == 'audio' and file_path:
            # Use tuple to specify filename to ensure it is sent correctly
            filename = name or os.path.basename(file_path)
            files = {'file': (filename, open(file_path, 'rb'))}
        elif data_type == 'audio_url' and audio_url:
            data['url'] = audio_url
            
        try:
            if files:
                return self._request('POST', f'/fs-containers/{container_id}/files',
                                    base_url=base_url, data=data, files=files)
            else:
                return self._request('POST', f'/fs-containers/{container_id}/files',
                                    base_url=base_url, json=data)
        finally:
            if files:
                files['file'][1].close()
    
    def delete_fs_files(self, container_id: int, region: str, file_ids: str) -> Dict:
        """Delete files from file scanning container"""
        return self._request('DELETE', f'/fs-containers/{container_id}/files/{file_ids}',
                            base_url=self._get_fs_base_url(region))
    
    def rescan_fs_files(self, container_id: int, region: str, file_ids: str) -> Dict:
        """Rescan files in file scanning container"""
        return self._request('PUT', f'/fs-containers/{container_id}/files/{file_ids}/rescan',
                            base_url=self._get_fs_base_url(region))
    
    # ==================== BM Custom Streams Projects ====================
    
    def list_bm_cs_projects(self, page: int = 1, per_page: int = 20,
                            region: Optional[str] = None,
                            types: Optional[str] = None) -> Dict:
        """List all BM custom streams projects"""
        params = {'page': page, 'per_page': per_page}
        if region:
            params['region'] = region
        if types:
            params['types'] = types
        return self._request('GET', '/bm-cs-projects', params=params)
    
    def get_bm_cs_project(self, project_id: int) -> Dict:
        """Get a specific BM custom streams project"""
        return self._request('GET', f'/bm-cs-projects/{project_id}')
    
    def create_bm_cs_project(self, name: str, region: str, buckets: List,
                             project_type: str = 'BM-ACRC',
                             external_ids: Optional[str] = None,
                             metadata_template: Optional[str] = None) -> Dict:
        """Create a new BM custom streams project"""
        data = {
            'name': name,
            'region': region,
            'buckets': buckets,
            'type': project_type
        }
        if external_ids:
            data['external_ids'] = external_ids
        if metadata_template:
            data['metadata_template'] = metadata_template
        return self._request('POST', '/bm-cs-projects', json=data)
    
    def update_bm_cs_project(self, project_id: int, name: Optional[str] = None,
                             buckets: Optional[List] = None,
                             external_ids: Optional[List] = None,
                             metadata_template: Optional[str] = None) -> Dict:
        """Update a BM custom streams project"""
        data = {}
        if name:
            data['name'] = name
        if buckets:
            data['buckets'] = buckets
        if external_ids:
            data['external_ids'] = external_ids
        if metadata_template:
            data['metadata_template'] = metadata_template
        return self._request('PUT', f'/bm-cs-projects/{project_id}', json=data)
    
    def delete_bm_cs_project(self, project_id: int) -> Dict:
        """Delete a BM custom streams project"""
        return self._request('DELETE', f'/bm-cs-projects/{project_id}')
    
    def set_bm_cs_result_callback(self, project_id: int, callback_url: str) -> Dict:
        """Set result callback URL for BM custom streams project"""
        data = {'result_callback_url': callback_url}
        return self._request('POST', f'/bm-cs-projects/{project_id}/result-callback', json=data)
    
    def set_bm_cs_state_notification_callback(self, project_id: int, 
                                              email: Optional[str] = None,
                                              frequency: Optional[int] = None,
                                              url: Optional[str] = None) -> Dict:
        """Set state notification callback for BM custom streams project"""
        data = {}
        if email:
            data['state_notification_email'] = email
        if frequency is not None:
            data['state_notification_email_frequency'] = frequency  # 0:High, 1:Low, 2:None
        if url:
            data['state_notification_url'] = url
        return self._request('POST', f'/bm-cs-projects/{project_id}/state-notification', json=data)
    
    # ==================== BM Custom Streams ====================
    
    def list_bm_streams(self, project_id: int, page: int = 1, per_page: int = 50,
                        timemap: Optional[int] = None,
                        state: Optional[str] = None,
                        search_value: Optional[str] = None,
                        sort: Optional[str] = None,
                        order: Optional[str] = None) -> Dict:
        """List streams in a BM custom streams project"""
        params = {'page': page, 'per_page': per_page}
        if timemap is not None:
            params['timemap'] = timemap
        if state:
            params['state'] = state
        if search_value:
            params['search_value'] = search_value
        if sort:
            params['sort'] = sort
        if order:
            params['order'] = order
        return self._request('GET', f'/bm-cs-projects/{project_id}/streams', params=params)
    
    def add_bm_stream(self, project_id: int, stream_urls: List[str], name: str,
                      config_id: int, user_defined: Optional[str] = None) -> Dict:
        """Add a stream to BM custom streams project"""
        data = {
            'stream_urls': stream_urls,
            'name': name,
            'config_id': config_id
        }
        if user_defined:
            data['user_defined'] = user_defined
        return self._request('POST', f'/bm-cs-projects/{project_id}/streams', json=data)
    
    def update_bm_stream(self, project_id: int, stream_id: str,
                         stream_urls: Optional[List[str]] = None,
                         name: Optional[str] = None,
                         config_id: Optional[int] = None) -> Dict:
        """Update a stream in BM custom streams project"""
        data = {}
        if stream_urls:
            data['stream_urls'] = stream_urls
        if name:
            data['name'] = name
        if config_id:
            data['config_id'] = config_id
        return self._request('PUT', f'/bm-cs-projects/{project_id}/streams/{stream_id}', json=data)
    
    def delete_bm_streams(self, project_id: int, stream_ids: str) -> Dict:
        """Delete streams from BM custom streams project"""
        return self._request('DELETE', f'/bm-cs-projects/{project_id}/streams/{stream_ids}')
    
    def pause_bm_streams(self, project_id: int, stream_ids: str) -> Dict:
        """Pause streams in BM custom streams project"""
        return self._request('PUT', f'/bm-cs-projects/{project_id}/streams/{stream_ids}/pause')
    
    def restart_bm_streams(self, project_id: int, stream_ids: str) -> Dict:
        """Restart streams in BM custom streams project"""
        return self._request('PUT', f'/bm-cs-projects/{project_id}/streams/{stream_ids}/restart')

    # ==================== BM Custom Streams Data ====================
    
    def get_bm_stream_state(self, project_id: int, stream_id: str,
                            timeoffset: Optional[int] = None,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> Dict:
        """Get the state of the stream"""
        params = {}
        if timeoffset is not None:
            params['timeoffset'] = timeoffset
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self._request('GET', f'/bm-cs-projects/{project_id}/streams/{stream_id}/state', params=params)
    
    def get_bm_stream_results(self, project_id: int, stream_id: str,
                              result_type: str = 'day',
                              date: Optional[str] = None,
                              min_duration: Optional[int] = None,
                              max_duration: Optional[int] = None,
                              isrc_country: Optional[str] = None,
                              with_false_positive: Optional[int] = None) -> Dict:
        """Get the stream monitoring results"""
        params = {'type': result_type}
        if date:
            params['date'] = date
        if min_duration is not None:
            params['min_duration'] = min_duration
        if max_duration is not None:
            params['max_duration'] = max_duration
        if isrc_country:
            params['isrc_country'] = isrc_country
        if with_false_positive is not None:
            params['with_false_positive'] = with_false_positive
        return self._request('GET', f'/bm-cs-projects/{project_id}/streams/{stream_id}/results', params=params)
    
    def get_bm_analytics(self, project_id: int, stats_type: str, result_type: str) -> Dict:
        """Get analytics data for the last 7 days"""
        params = {
            'stats_type': stats_type,
            'result_type': result_type
        }
        return self._request('GET', f'/bm-cs-projects/{project_id}/analytics/results', params=params)
    
    def add_bm_stream_user_report(self, project_id: int, stream_id: str, data: List[Dict]) -> Dict:
        """Insert user results"""
        payload = {'data': data}
        return self._request('POST', f'/bm-cs-projects/{project_id}/streams/{stream_id}/user-reports', json=payload)
    
    def get_bm_stream_recording(self, project_id: int, stream_id: str,
                                timestamp_utc: str, played_duration: int,
                                record_before: int = 0, record_after: int = 0) -> Dict:
        """Get the recording of the results"""
        params = {
            'timestamp_utc': timestamp_utc,
            'played_duration': played_duration,
            'record_before': record_before,
            'record_after': record_after
        }
        return self._request('GET', f'/bm-cs-projects/{project_id}/streams/{stream_id}/recordings', params=params)

    # ==================== BM Database Projects ====================
    
    def list_bm_db_projects(self, region: Optional[str] = None) -> Dict:
        """List all BM Database projects"""
        params = {}
        if region:
            params['region'] = region
        return self._request('GET', '/bm-bd-projects', params=params)

    def create_bm_db_project(self, name: str, region: str, buckets: List[int]) -> Dict:
        """Create a new BM Database project"""
        payload = {
            'name': name,
            'region': region,
            'buckets': buckets
        }
        return self._request('POST', '/bm-bd-projects', json=payload)

    def update_bm_db_project(self, project_id: int, name: Optional[str] = None, buckets: Optional[List[int]] = None) -> Dict:
        """Update a BM Database project"""
        payload = {}
        if name:
            payload['name'] = name
        if buckets:
            payload['buckets'] = buckets
        return self._request('PUT', f'/bm-bd-projects/{project_id}', json=payload)

    def delete_bm_db_project(self, project_id: int) -> Dict:
        """Delete a BM Database project"""
        return self._request('DELETE', f'/bm-bd-projects/{project_id}')

    def set_bm_db_result_callback(self, project_id: int, result_callback_url: str,
                                  result_callback_send_noresult: int = 0,
                                  result_callback_result_type: int = 0) -> Dict:
        """Set result callback URL for BM Database project"""
        payload = {
            'result_callback_url': result_callback_url,
            'result_callback_send_noresult': result_callback_send_noresult,
            'result_callback_result_type': result_callback_result_type
        }
        return self._request('POST', f'/bm-bd-projects/{project_id}/result-callback', json=payload)

    def set_bm_db_state_notification_callback(self, project_id: int, state_callback_url: str) -> Dict:
        """Set state notification callback for BM Database project"""
        payload = {
            'state_callback_url': state_callback_url
        }
        return self._request('POST', f'/bm-bd-projects/{project_id}/state-notification', json=payload)

    # ==================== BM Database Channels ====================
    
    def list_bm_db_channels(self, project_id: int, state: str = 'All', timemap: Optional[str] = None,
                            search_type: Optional[str] = None, search_value: Optional[str] = None,
                            page: int = 1) -> Dict:
        """List channels in BM Database project"""
        params = {'state': state, 'page': page}
        if timemap:
            params['timemap'] = timemap
        if search_type and search_value:
            params['search_type'] = search_type
            params['search_value'] = search_value
        return self._request('GET', f'/bm-bd-projects/{project_id}/channels', params=params)

    def add_bm_db_channels(self, project_id: int, channels: List[int]) -> Dict:
        """Add channels to BM Database project"""
        payload = {'channels': channels}
        return self._request('POST', f'/bm-bd-projects/{project_id}/channels', json=payload)

    def delete_bm_db_channels(self, project_id: int, channel_ids: str) -> Dict:
        """Delete channels from BM Database project"""
        return self._request('DELETE', f'/bm-bd-projects/{project_id}/channels/{channel_ids}')

    def set_bm_db_channel_custom_id(self, project_id: int, channel_id: int, custom_id: str) -> Dict:
        """Set custom_id for a channel"""
        params = {'custom_id': custom_id}
        return self._request('POST', f'/bm-bd-projects/{project_id}/channels/{channel_id}/user-defined', params=params)

    # ==================== BM Database Channels Data ====================
    
    def get_bm_db_channel_results(self, project_id: int, channel_id: int, result_type: str = 'day',
                                  date: Optional[str] = None, min_duration: Optional[int] = None,
                                  max_duration: Optional[int] = None, isrc_country: Optional[str] = None,
                                  with_false_positive: Optional[int] = None) -> Dict:
        """Get non-real-time results of channel monitoring"""
        params = {'type': result_type}
        if date:
            params['date'] = date
        if min_duration is not None:
            params['min_duration'] = min_duration
        if max_duration is not None:
            params['max_duration'] = max_duration
        if isrc_country:
            params['isrc_country'] = isrc_country
        if with_false_positive is not None:
            params['with_false_positive'] = with_false_positive
        return self._request('GET', f'/bm-bd-projects/{project_id}/channels/{channel_id}/results', params=params)

    def get_bm_db_channel_realtime_results(self, project_id: int, channel_id: int) -> Dict:
        """Get real-time results of channel monitoring"""
        return self._request('GET', f'/bm-bd-projects/{project_id}/channels/{channel_id}/realtime_results')

    def get_bm_db_channel_state(self, project_id: int, channel_id: int,
                                timeoffset: Optional[int] = None,
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None) -> Dict:
        """Get the state of the channel"""
        params = {}
        if timeoffset is not None:
            params['timeoffset'] = timeoffset
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self._request('GET', f'/bm-bd-projects/{project_id}/channels/{channel_id}/state', params=params)

    def get_bm_db_analytics(self, project_id: int, stats_type: str, result_type: str) -> Dict:
        """Get analytics data for the last 7 days"""
        params = {
            'stats_type': stats_type,
            'result_type': result_type
        }
        return self._request('GET', f'/bm-bd-projects/{project_id}/analytics/results', params=params)

    def add_bm_db_channel_user_report(self, project_id: int, channel_id: int, data: List[Dict]) -> Dict:
        """Insert user results"""
        payload = {'data': data}
        return self._request('POST', f'/bm-bd-projects/{project_id}/channels/{channel_id}/user-reports', json=payload)

    def get_bm_db_channel_recording(self, project_id: int, channel_id: int,
                                    timestamp_utc: str, played_duration: int,
                                    record_before: int = 0, record_after: int = 0) -> Dict:
        """Get the recording of the results"""
        params = {
            'timestamp_utc': timestamp_utc,
            'played_duration': played_duration,
            'record_before': record_before,
            'record_after': record_after
        }
        return self._request('GET', f'/bm-bd-projects/{project_id}/channels/{channel_id}/recordings', params=params)

    # ==================== UCF Projects ====================

    def list_ucf_projects(self, region: Optional[str] = None) -> Dict:
        """List all UCF projects"""
        params = {}
        if region:
            params['region'] = region
        return self._request('GET', '/ucf-projects', params=params)

    def create_ucf_project(self, name: str, region: str, project_type: str = 'BM',
                           config: Optional[Dict] = None) -> Dict:
        """Create a new UCF project"""
        payload = {
            'name': name,
            'region': region,
            'type': project_type
        }
        if config:
            payload['config'] = config
        return self._request('POST', '/ucf-projects', json=payload)

    def update_ucf_project(self, project_id: int, name: Optional[str] = None,
                           config: Optional[Dict] = None) -> Dict:
        """Update a UCF project"""
        payload = {}
        if name:
            payload['name'] = name
        if config:
            payload['config'] = config
        return self._request('PUT', f'/ucf-projects/{project_id}', json=payload)

    def delete_ucf_project(self, project_id: int) -> Dict:
        """Delete a UCF project"""
        return self._request('DELETE', f'/ucf-projects/{project_id}')

    # ==================== UCF BM Streams ====================

    def list_ucf_streams(self, project_id: int, page: int = 1, per_page: int = 10) -> Dict:
        """List UCF BM streams"""
        params = {'page': page, 'per_page': per_page}
        return self._request('GET', f'/ucf-projects/{project_id}/streams', params=params)

    def import_ucf_bm_streams(self, project_id: int, bm_stream_ids: List[str],
                              origin_from: str, bm_project_id: int) -> Dict:
        """Import BM streams to UCF project"""
        payload = {
            'bm_stream_ids': bm_stream_ids,
            'from': origin_from,
            'bm_project_id': bm_project_id
        }
        return self._request('POST', f'/ucf-projects/{project_id}/streams', json=payload)

    def delete_ucf_bm_streams(self, project_id: int, stream_ids: str) -> Dict:
        """Delete UCF BM streams"""
        return self._request('DELETE', f'/ucf-projects/{project_id}/streams/{stream_ids}')

    # ==================== UCF Results ====================

    def list_ucf_results(self, project_id: int, page: int = 1, per_page: int = 10,
                         begin_date: Optional[str] = None, end_date: Optional[str] = None,
                         sortby: Optional[str] = None, order: Optional[str] = None,
                         status: Optional[str] = None, min_duration: Optional[str] = None,
                         max_duration: Optional[str] = None, streams: Optional[str] = None,
                         ucf_id: Optional[str] = None, label: Optional[str] = None,
                         label_value: Optional[str] = None) -> Dict:
        """List UCF results"""
        params = {'page': page, 'per_page': per_page}
        if begin_date: params['begin_date'] = begin_date
        if end_date: params['end_date'] = end_date
        if sortby: params['sortby'] = sortby
        if order: params['order'] = order
        if status: params['status'] = status
        if min_duration: params['min'] = min_duration
        if max_duration: params['max'] = max_duration
        if streams: params['streams'] = streams
        if ucf_id: params['ucf_id'] = ucf_id
        if label: params['label'] = label
        if label_value: params['label_value'] = label_value
        return self._request('GET', f'/ucf-projects/{project_id}/results', params=params)

    def get_ucf_result(self, project_id: int, ucf_id: str) -> Dict:
        """Get one UCF item"""
        return self._request('GET', f'/ucf-projects/{project_id}/results/{ucf_id}')

    def get_ucf_result_details(self, project_id: int, ucf_id: int, page: int = 1,
                               per_page: int = 10, begin_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> Dict:
        """Get UCF item details"""
        params = {'page': page, 'per_page': per_page}
        if begin_date: params['begin_date'] = begin_date
        if end_date: params['end_date'] = end_date
        return self._request('GET', f'/ucf-projects/{project_id}/results/{ucf_id}/details', params=params)

    def get_ucf_record_url(self, project_id: int, ucf_id: str, extend: int = 20) -> Dict:
        """Get UCF record URL"""
        params = {'extend': extend}
        return self._request('GET', f'/ucf-projects/{project_id}/results/{ucf_id}/record', params=params)

    def delete_ucf_item(self, project_id: int, ucf_id: int, reserved: int = 0) -> Dict:
        """Delete or reserve a UCF item"""
        params = {'reserved': reserved}
        return self._request('DELETE', f'/ucf-projects/{project_id}/results/{ucf_id}', params=params)

    def set_ucf_item_pending(self, project_id: int, ucf_id: int) -> Dict:
        """Make a UCF item status pending"""
        return self._request('POST', f'/ucf-projects/{project_id}/results/{ucf_id}/pending')


class APIError(Exception):
    """API Error exception"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
