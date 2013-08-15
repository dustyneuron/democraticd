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
        self.next_api_time = time.time()
                
        print('GitHub username/password is ' + username + '/' + password)
        
    def api_notifications(self):
        return self.api_call('GET', self.base_url + '/notifications')
                    
    def api_call(self, method, url):
        current_time = time.time()
        if self.next_api_time > current_time:
            time.sleep(long(self.next_api_time - current_time))
    
        req = urllib.request.Request(url=url, method=method)
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
            
