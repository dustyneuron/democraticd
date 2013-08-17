#!/usr/bin/env python3.3

import demod.config

import functools
    
class PullRequest:
    def __init__(self, data):
        self.repo = data['repository']['name']
        self.title = data['subject']['title']
        self.pull_api_url = data['subject']['url']
        self.repo_type = None
        
    def fill(self, data):
        if data['base']['repo']['name'] != self.repo:
            raise Exception('Full pull request name does not match')
        
        self.pull_id = data['number']
        self.description = data['body']
        self.ref = data['head']['ref']
        self.sha = data['head']['sha']
        self.base_ref = data['base']['ref']
        self.base_sha = data['base']['sha']
        self.repo_git_url = data['head']['repo']['clone_url']
        self.repo_api_url = data['head']['repo']['url']
        

def create_pull_requests(notifications, package_set, module_set):
    repo_dict = {}
    for n in notifications:
        if n['subject']['type'] == 'PullRequest':
            pr = PullRequest(n)
            if pr.repo in package_set:
                pr.repo_type = 'package'
            elif pr.repo in module_set:
                pr.repo_type = 'module'
            else:
                print('Ignoring pull request for non-daemon repository "' + pr.repo + '"')
                pr = None
                
            if pr:
                if pr.repo not in repo_dict:
                    repo_dict[pr.repo] = []
                repo_dict[pr.repo].append(pr)
                
    return repo_dict


def fill_pull_requests(hosted_git, repo_dict):
    for repo in repo_dict.keys():
        list_pull_requests = hosted_git.list_pull_requests(repo)
        for pr in repo_dict[repo]:
            filled = False
            for full_pr in list_pull_requests:
                if pr.pull_api_url == full_pr['url']:
                    pr.fill(full_pr)
                    filled = True
                    break
            if not filled:
                raise Exception('No matching full pull request for ' + str(pr.pull_api_url))


def get_new_pull_requests(config, hosted_git):
    notifications = hosted_git.get_new_notifications(mark_read=False)
    #import json
    #with open('test/notifications.json') as f:
    #    notifications = json.loads(f.read())
    package_set = config.get_package_set()
    module_set = config.get_module_set()
    
    repo_dict = create_pull_requests(notifications, package_set, module_set)
    fill_pull_requests(hosted_git, repo_dict)
    
    return repo_dict


config = demod.config.Config()
hosted_git = config.create_hosted_git()

repo_dict = get_new_pull_requests(config, hosted_git)

for pr in functools.reduce(lambda acc, x: acc + x, repo_dict.values()):
    print('PR #' + str(pr.pull_id) + ': ' + pr.title)

# MVP: check for notifications, filter out pull requests,
# new pull reqs -> save (in-memory) new proposals,
# post a comment back

# MVP 2:
# download new pulls into local git repo
# merge + push back to github
