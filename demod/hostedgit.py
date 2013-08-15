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
    

class PullRequest:
    def __init__(self, repo_name, github_data):
        if not github_data.mergeable:
            raise HostedGitError('Pull request ' + github_data['url']
                + ' marked not mergeable')
            
        self.repo_name = repo_name
        self.title = github_data['title']
        self.description = github_data['body']
        self.pull = {}
        self.pull.ref = github_data['head']['ref']
        self.pull.sha = github_data['head']['sha']
        self.pull.clone_url = github_data['head']['repo']['clone_url']



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
        base64string = base64.b64encode((self.username + ':' + self.password).encode())
        req.add_header("Authorization", "Basic %s" % base64string)
        try:
            result = urllib.request.urlopen(req)
        except urllib.error.HTTPError as err:
            print(err.info())
            raise
            
        if not result:
            raise HostedGitError('urllib request did not return a result')
        
        print(result.info())
        
        if result.getheader('X-poll-interval'):
            self.next_api_time = time.time() + 2 * float(result.getheader('X-poll-interval'))
        
        status = result.status
        if status != 200 or status != 304:
            raise HostedGitError('API HTTP error code ' + str(status))
            
        return json.loads(result.read())
        
        
    def do_loop(self):
        while True:
            # do api poll!
            data = self.api_call('GET', '/notifications')
            
