#!/usr/bin/env python3.3

import json
import urllib3
import base64
import time

class HostedGitError(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return repr.repr(self.value)
        

class HostedGit:
    def __init__(self, username, password):
        self.base_url = 'api.github.com'        
        self.username = username
        self.password = password
        self.next_notify_time = time.time()
        self.last_modified = {}
        self.conn_pool = None
        
    def _api_call(self, url, method='GET', headers={}):
        print('_api_call(' + method + ', ' + url + ')')
        
        auth = bytes.decode(base64.b64encode((self.username + ':' + self.password).encode()))
        headers['Authorization'] = 'Basic %s' % auth
        headers['User-Agent'] = 'democraticd (https://github.com/dustyneuron/democraticd)'
        headers['Accept'] = '*/*'
        last_modified_key = method + ' ' + url
        if last_modified_key in self.last_modified:
            headers['If-Modified-Since'] = self.last_modified[last_modified_key]
        print(headers)
        print('\n')

        if not self.conn_pool:
            self.conn_pool = urllib3.HTTPSConnectionPool(self.base_url, maxsize=1)
        
        try:
            result = self.conn_pool.request(method, url, headers=headers)
        except urllib.error.HTTPError as err:
            print(err.headers)
            raise
        if not result:
            raise HostedGitError('urllib request did not return a result')
            
        if result.headers.get('last-modified'):
            self.last_modified[last_modified_key] = result.headers.get('last-modified')
        
        print(result.headers)
        return result
        
    def _return_json(self, result):
        if result.status == 304:
            return []
        data = json.loads(result.data.decode('utf-8'))
        result.release_conn()
        if len(data) >= 30:
            raise HostedGitError('TODO: implement pagination')
        return data

    def api_notifications(self):
        current_time = time.time()
        if self.next_notify_time > current_time:
            sleep_time = int(self.next_notify_time - current_time)
            print('Sleeping for ' + str(sleep_time) + ' secs because of X-poll-interval')
            time.sleep(sleep_time)
            
        result = self._api_call('/notifications')
                
        if result.headers.get('x-poll-interval'):
            time_to_wait = float(result.headers.get('x-poll-interval'))
            self.next_notify_time = time.time() + time_to_wait
        
        return self._return_json(result)
        
    def api_list_pull_requests(self, repo):
        result = self._api_call('/repos/' + self.username + '/' + repo + '/pulls')
        return self._return_json(result)
        
