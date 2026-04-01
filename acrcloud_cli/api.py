"""
ACRCloud API Client
"""

import requests
import json
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
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        # Handle files separately for multipart/form-data
        if 'files' in kwargs:
            # Remove Content-Type header for multipart requests
            headers = dict(self.session.headers)
            headers.pop('Content-Type', None)
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
        
        url = f"{base_url}/fs-containers/{container_id}/files"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_fs_file(self, container_id: int, region: str, file_id: str) -> Dict:
        """Get a specific file scanning file"""
        base_url = self._get_fs_base_url(region)
        url = f"{base_url}/fs-containers/{container_id}/files/{file_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def upload_fs_file(self, container_id: int, region: str,
                       file_path: Optional[str] = None,
                       audio_url: Optional[str] = None,
                       data_type: str = 'audio') -> Dict:
        """Upload a file to file scanning container"""
        base_url = self._get_fs_base_url(region)
        url = f"{base_url}/fs-containers/{container_id}/files"
        
        data = {'data_type': data_type}
        files = None
        
        if data_type == 'audio' and file_path:
            files = {'file': open(file_path, 'rb')}
        elif data_type == 'audio_url' and audio_url:
            data['url'] = audio_url
        
        try:
            if files:
                headers = dict(self.session.headers)
                headers.pop('Content-Type', None)
                response = self.session.post(url, data=data, files=files, headers=headers)
            else:
                response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        finally:
            if files:
                for f in files.values():
                    f.close()
    
    def delete_fs_files(self, container_id: int, region: str, file_ids: str) -> Dict:
        """Delete files from file scanning container"""
        base_url = self._get_fs_base_url(region)
        url = f"{base_url}/fs-containers/{container_id}/files/{file_ids}"
        response = self.session.delete(url)
        response.raise_for_status()
        return {}
    
    def rescan_fs_files(self, container_id: int, region: str, file_ids: str) -> Dict:
        """Rescan files in file scanning container"""
        base_url = self._get_fs_base_url(region)
        url = f"{base_url}/fs-containers/{container_id}/files/{file_ids}/rescan"
        response = self.session.put(url)
        response.raise_for_status()
        return response.json()
    
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


class APIError(Exception):
    """API Error exception"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
