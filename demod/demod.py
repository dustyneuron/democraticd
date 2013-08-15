#!/usr/bin/env python3.3

import demod.config
    
class PullRequest:
    def __init__(self, data):
        self.repo_name = data['repository']['name']
        self.title = data['subject']['title']
        self.api_url = data['subject']['url']
        
    def fill_info(self, data):
        self.pull_ref = data['head']['ref']
        self.pull_sha = data['head']['sha']
        self.pull_clone_url = data['head']['repo']['clone_url']


    
def handle_pull(module_or_package_name, pull_request):
    print('handle_pull(module_or_package_name=' + module_or_package_name + ', pull_request)')


config = demod.config.Config()

package_set = config.get_package_set()
module_set = config.get_module_set()

hosted_git = config.create_hosted_git()
repos = module_set.union(package_set)
hosted_git.watch_repositories(repos, handle_pull)


notifications = hosted_git.api_call('notifications')

import json
with open('test/notifications.json') as f:
    notifications = json.loads(f.read())
    

for n in notifications:
    if n['subject']['type'] == 'PullRequest':
        pr = PullRequest(n)



# MVP: check for notifications, filter out pull requests,
# new pull reqs -> save (in-memory) new proposals,
# post a comment back

# MVP 2:
# download new pulls into local git repo
# merge + push back to github
