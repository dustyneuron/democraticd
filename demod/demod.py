#!/usr/bin/env python3.3

import demod.config
    
class PullRequest:
    def __init__(self, data):
        self.repo = data['repository']['name']
        self.title = data['subject']['title']
        self.pull_api_url = data['subject']['url']
        self.repo_type = None
        self.filled = False
        
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
        self.filled = True



config = demod.config.Config()

package_set = config.get_package_set()
module_set = config.get_module_set()

hosted_git = config.create_hosted_git()
repos = module_set.union(package_set)


#notifications = hosted_git.api_notifications()

import json
with open('test/notifications.json') as f:
    notifications = json.loads(f.read())


pull_requests = []
pr_repos = set([])
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
            pr_repos.add(pr.repo)
            pull_requests.append(pr)
            

for repo in pr_repos:
    list_pull_requests = hosted_git.api_list_pull_requests(repo)
    for pr in pull_requests:
        if not pr.filled:
            for full_pr in list_pull_requests:
                if pr.pull_api_url == full_pr['url']:
                    pr.fill(full_pr)
                    break
                    



# MVP: check for notifications, filter out pull requests,
# new pull reqs -> save (in-memory) new proposals,
# post a comment back

# MVP 2:
# download new pulls into local git repo
# merge + push back to github
