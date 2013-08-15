#!/usr/bin/env python3.3

import json
import httplib2
import urllib
import time

class HostedGitError(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return repr.repr(self.value)
    

class PullRequest:
    def __init__(self, repo_name, github_data):
        if not github_data.mergeable:
            raise HostedGitError('Pull request ' + github_data.url
                + ' marked not mergeable')
            
        self.repo_name = repo_name
        self.title = github_data.title
        self.description = github_data.body
        self.pull = {}
        self.pull.ref = github_data.head.ref
        self.pull.sha = github_data.head.sha
        self.pull.clone_url = github_data.head.repo.clone_url



class HostedGit:
    def __init__(self, username, password, cache_dir):
        self.username = username
        self.password = password
        self.repo_set = set([])
        self.callback = None
        self.next_api_time = time.time()

        self.http = httplib2.Http(cache_dir)
        self.http.add_credentials(username, password, 'api.github.com')
        
    def watch_repositories(self, repo_names, callback):
        self.repo_set = set(repo_names)
        self.callback = callback
            
    def api_call(self, action, path):
        current_time = time.time()
        if self.next_api_time > current_time:
            time.sleep(long(self.next_api_time - current_time))
        
        url = 'https://api.github.com' + path
        
        r, content = self.http.request(url, method=action)
        if not r or not content:
            raise HostedGitError('httplib2 request did not return a request, content tuple')
            
        if 'x-poll-interval' in r:
            self.next_api_time = time.time() + float(r['x-poll-interval'])
        
        status = int(r['status'])
        if status != 200 or status != 304:
            raise HostedGitError('API HTTP error code ' + status)
            
        return json.loads(content)
        
        
    def do_loop(self):
        while True:
            # do api poll!
            data = self.api_call('GET', '/notifications')
            
