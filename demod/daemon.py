#!/usr/bin/env python

import demod.config

import functools
    
class PullRequest:
    state_EMPTY = 0
    state_NEW = 1
    state_FILLED = 2
    state_COMMENTED = 3
    
    def __init__(self):
        pass
        
    def __init__(self, data=None):
        if data:
            self.repo = data['repository']['name']
            self.title = data['subject']['title']
            self.pull_api_url = data['subject']['url']
            self.repo_type = None
            self.status = self.state_NEW
        else:
            self.status = self.state_EMPTY
            
    def is_more_recent_than(self, pr):
        return (self.status > pr.status)
        
    def fill(self, data):
        if data['base']['repo']['name'] != self.repo:
            raise Exception('Full pull request name does not match')
        
        self.issue_id = data['number']
        self.description = data['body']
        self.ref = data['head']['ref']
        self.sha = data['head']['sha']
        self.base_ref = data['base']['ref']
        self.base_sha = data['base']['sha']
        self.repo_git_url = data['head']['repo']['clone_url']
        self.repo_api_url = data['head']['repo']['url']
        self.status = self.state_FILLED
        
    def set_vote_url(self):
        self.vote_url = 'http://someurl.com/vote/' + self.repo + '/' + str(self.issue_id) + '/'
        
    def set_comment_log(self, data):
        self.comment_id = data['id']
        self.comment_api_url = data['url']
        self.comment_body = data['body']
        self.status = self.state_COMMENTED
        

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
    
    package_set = config.get_package_set()
    module_set = config.get_module_set()
    repo_dict = create_pull_requests(notifications, package_set, module_set)
    fill_pull_requests(hosted_git, repo_dict)
    
    return repo_dict

def update_pull_request_list(old_rp_list, new_rp_list):
    new_list = list(old_rp_list)
    for new_rp in new_rp_list:
        issue_id = new_rp.issue_id
        matching_prs = [idx for idx in list(range(len(old_rp_list))) if old_rp_list[idx].issue_id == issue_id]
        if len(matching_prs) == 0:
            new_list.append(new_rp)
        elif len(matching_prs) == 1:
            if new_rp.is_more_recent_than(old_rp_list[matching_prs[0]]):
                old_rp_list[matching_prs[0]] = new_rp
        else:
            raise Exception('pr_list has multiple prs for a single issue id')
    return new_list

def comment_on_pull_requests(hosted_git, repo_dict):
    for pr in functools.reduce(lambda acc, x: acc + x, repo_dict.values()):
        if pr.status == pr.state_FILLED:
            # Would interact with db at this point, the vote url needs to be live
            pr.set_vote_url()
            hosted_git.create_pull_request_comment(pr)

    
def daemon_loop(config, hosted_git):
    while True:
        print('Starting daemon loop')
        repo_dict = {}
        for repo in config.get_repo_set():
            print('Reading saved pull requests for "' + str(repo) + '"')
            repo_dict[repo] = config.read_pull_requests(repo, PullRequest)

        print('Getting new pull request notifications from GitHub API')
        new_repo_dict = get_new_pull_requests(config, hosted_git)
        
        for repo in repo_dict.keys():
            if repo in new_repo_dict:
                repo_dict[repo] = update_pull_request_list(repo_dict[repo], new_repo_dict[repo])
                
        print('Commenting on pull requests')
        comment_on_pull_requests(hosted_git, repo_dict)
        
        for (repo, pr_list) in repo_dict.items():
            print('Saving pull requests for "' + str(repo) + '"')
            config.write_pull_requests(repo, pr_list)

        
def go():
    config = demod.config.Config()
    hosted_git = config.create_hosted_git()
    daemon_loop(config, hosted_git)


# MVP:
# Is there a non-web UI that makes sense? eg for a single dev
# doing core work...
#
# single-dev workflow: "-s --standalone"
# open a github pull request,
# daemon picks up on it, saves it to a config file in case daemon dies,
# and comments 'run $ demod approve 3'
# Dev runs this command, and the daemon merges, installs, + pushes back
# to github
#
##
#
# download new pulls into local git repo
# merge, install + push back to github



