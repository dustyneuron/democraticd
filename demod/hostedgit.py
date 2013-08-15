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
        base_api = 'https://api.github.com'
        self.api_calls = {
            'notifications': {
                'method':   'GET',
                'url':      base_api + '/notifications',
            },
        }
        self.api_urls = [d['url'] for d in self.api_calls.values()]
        
        self.username = username
        self.password = password
        self.repo_set = set([])
        self.callback = None
        self.next_api_time = time.time()
                
        print('GitHub username/password is ' + username + '/' + password)
        
    def watch_repositories(self, repo_names, callback):
        self.repo_set = set(repo_names)
        self.callback = callback
            
    def api_call(self, api_call):
        if api_call not in self.api_calls:
            raise HostedGitError('No such api call ' + str(api_call))
        
        current_time = time.time()
        if self.next_api_time > current_time:
            time.sleep(long(self.next_api_time - current_time))
    
        req = urllib.request.Request(url=self.api_calls[api_call]['url'], method=self.api_calls[api_call]['method'])
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
        
        print(result.info())
        
        if result.info().get('X-poll-interval'):
            time_to_wait = 2 * float(result.info().get('X-poll-interval'))
            self.next_api_time = time.time() + time_to_wait
            print('Will wait ' + str(time_to_wait) + ' secs before next api call')
        
        status = int(result.getcode())
        if (status == 200) or (status == 304):
            return json.loads(result.read().decode('utf-8'))
        else:
            raise HostedGitError('API HTTP error code ' + str(status))
        
        
        
    def do_loop(self):
        while True:
            # do api poll!
            data = self.api_call('GET', '/notifications')
            
