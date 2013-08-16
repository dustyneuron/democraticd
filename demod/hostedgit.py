#!/usr/bin/env python3.3

import json
import urllib.request
import urllib.error
import base64
import time

class HostedGitError(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return repr.repr(self.value)
        

class HostedGit:
    def __init__(self, username, password):
        self.base_url = 'https://api.github.com'        
        self.username = username
        self.password = password
        self.next_notify_time = time.time()
        self.last_modified = {}
        
    def _api_call(self, url, method='GET', headers={}):
        print('_api_call(' + method + ', ' + url + ')')
        
        auth = bytes.decode(base64.b64encode((self.username + ':' + self.password).encode()))
        headers['Authorization'] = 'Basic %s' % auth
        headers['User-Agent'] = 'curl/7.29.0'
        headers['Accept'] = '*/*'
        last_modified_key = method + ' ' + url
        if last_modified_key in self.last_modified:
            headers['If-Modified-Since'] = self.last_modified[last_modified_key]
        
        req = urllib.request.Request(url=self.base_url + url, method=method)
        for (k, v) in headers.items():
            req.add_header(k, v)
        
        print(req.headers)
        print('\n')
        
        try:
            result = urllib.request.urlopen(req)
        except urllib.error.HTTPError as err:
            if err.getcode() == 304:
                result = err
            else:
                print(err.info())
                raise
        if not result:
            raise HostedGitError('urllib request did not return a result')
            
        if result.info().get('Last-Modified'):
            self.last_modified[last_modified_key] = result.info().get('Last-Modified')
        
        print(result.info())
        return result
        
    def _get_json(self, result):
        if result.getcode() == 304:
            return []
        data = json.loads(result.read().decode('utf-8'))
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
                
        if result.info().get('X-poll-interval'):
            time_to_wait = float(result.info().get('X-poll-interval'))
            self.next_notify_time = time.time() + time_to_wait
        
        return self._get_json(result)
        
    def api_list_pull_requests(self, repo):
        result = self._api_call('/repos/' + self.username + '/' + repo + '/pulls')
        return self._get_json(result)
        
