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
        
    def _api_call(self, method, url):
        print('_api_call(' + method + ', ' + url + ')')
        
        req = urllib.request.Request(url=self.base_url + url, method=method)
        auth = bytes.decode(base64.b64encode((self.username + ':' + self.password).encode()))
        req.add_header('Authorization', 'Basic %s' % auth)
        req.add_header('User-Agent', 'curl/7.29.0')
        req.add_header('Accept', '*/*')
        #print(req.headers)
        #print('\n')
        
        try:
            result = urllib.request.urlopen(req)
        except urllib.error.HTTPError as err:
            print(err.info())
            raise
        if not result:
            raise HostedGitError('urllib request did not return a result')
        
        #print(result.info())
        return result
        
    def _parse_json(self, json_data):
        data = json.loads(json_data.decode('utf-8'))
        if len(data) >= 30:
            raise HostedGitError('TODO: implement pagination')
        return data

    def api_notifications(self):
        current_time = time.time()
        if self.next_notify_time > current_time:
            time.sleep(long(self.next_notify_time - current_time))
    
        result = self._api_call('GET', '/notifications')
        
        if result.info().get('X-poll-interval'):
            time_to_wait = 2 * float(result.info().get('X-poll-interval'))
            self.next_notify_time = time.time() + time_to_wait
            print('Will wait ' + str(time_to_wait) + ' secs before next notify call')
        
        return self._parse_json(result.read())
        
    def api_list_pull_requests(self, repo):
        result = self._api_call('GET', '/repos/' + self.username + '/' + repo + '/pulls')
        return self._parse_json(result.read())
        
