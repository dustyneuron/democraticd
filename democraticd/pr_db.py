from __future__ import print_function, unicode_literals

from democraticd.pullrequest import PullRequest, prs_to_json, prs_from_json


def find_pull_request_idx(pr_list, key):
    matching_prs = [idx for idx in range(len(pr_list)) if pr_list[idx].key() == key]
    if len(matching_prs) == 0:
        return -1
    elif len(matching_prs) == 1:
        return matching_prs[0]
    else:
        raise Exception('pr_list has multiple prs for a single key')


def update_pull_request_list(old_pr_list, new_pr_list):
    result_list = list(old_pr_list)
    for new_pr in new_pr_list:
        idx = find_pull_request_idx(result_list, new_pr.key())
        if idx == -1:
            result_list.append(new_pr)
        elif new_pr.is_more_recent_than(result_list[idx]):
            result_list[idx] = new_pr
        else:
            result_list[idx].notify_update()
            
    return result_list


class PullRequestDB:
    def __init__(self, config):
        self.config = config
        self.repo_dict = {}
        
    def read_pull_requests(self, repo_list=None):
        if not repo_list:
            repo_list = self.repos()
        elif type(repo_list) != type([]):
            repo_list = [repo_list]

        for repo in repo_list:
            filename = self.config.get_pull_requests_filename(repo)
            with open(filename, 'rt') as f:
                pr_list = prs_from_json(f.read())
            
            self.repo_dict[repo] = pr_list
        
    def write_pull_requests(self, repo_list=None):
        if not repo_list:
            repo_list = self.repos()
        elif type(repo_list) != type([]):
            repo_list = [repo_list]
        
        for repo in repo_list:
            data = prs_to_json(self.pull_requests(repo)).encode()
            
            filename = self.config.get_pull_requests_filename(repo)
            with open(filename, 'wb') as f:
                f.write(data)
            
    def pull_requests(self, repo_list=None):
        if not repo_list:
            repo_list = self.repos()
        elif type(repo_list) != type([]):
            repo_list = [repo_list]

        r = []
        for repo in repo_list:
            r = r + self.repo_dict[repo]
        return r
        
    def repos(self):
        return self.repo_dict.keys()
        
    def find_pull_request(self, repo, key):
        idx = find_pull_request_idx(self.repo_dict[repo], key)
        return self.repo_dict[repo][idx]
        
    def create_pull_requests(self, notifications):
        package_set = self.config.get_package_set()
        module_set = self.config.get_module_set()
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

        
    def get_new_pull_requests(self, github_api):
        notifications, do_quit = github_api.get_new_notifications(mark_read=self.config.mark_read)
        if do_quit:
            return (None, do_quit)
        return (self.create_pull_requests(notifications), do_quit)
        
    def notify_voting_func(self, pr):
        print('notify_voting_func ' + str(pr.key()))

    def fill_pull_requests(self, github_api):            
        for repo in self.repos():
            need_fill = False
            for pr in self.pull_requests(repo):
                if (pr.state < pr.state_idx('FILLED')) or pr.needs_update:
                    need_fill = True
                    break
                    
            if need_fill:
                list_pull_requests = github_api.list_pull_requests(repo)
                for pr in self.pull_requests(repo):
                    found_pr_data = None
                    for pr_data in list_pull_requests:
                        if pr.pull_api_url == pr_data['url']:
                            found_pr_data = pr_data
                            break

                    pr.update(found_pr_data, self.notify_voting_func)
                        
                self.write_pull_requests(repo)

    def comment_on_pull_requests(self, github_api):
        for repo in self.repos():
            for pr in self.pull_requests(repo):
                if pr.state == pr.state_idx('FILLED'):
                    # Would interact with db at this point, the vote url needs to be live
                    pr.set_vote_url()
                    github_api.create_pull_request_comment(pr)
            
            self.write_pull_requests(repo)

    def do_github_actions(self, github_api):
        
        print('At top of daemon loop')
        for repo in self.config.get_repo_set():
            print('Reading saved pull requests for "' + str(repo) + '"')
            self.read_pull_requests(repo)

        print('Getting new pull request notifications from GitHub API')
        new_repo_dict, do_quit = self.get_new_pull_requests(github_api)
        if do_quit:
            return
        if new_repo_dict:
            for repo in self.repos():
                if repo in new_repo_dict:
                    self.repo_dict[repo] = update_pull_request_list(self.repo_dict[repo], new_repo_dict[repo])
                    self.write_pull_requests(repo)
                
        print('Filling any pull requests if needed')
        self.fill_pull_requests(github_api)
                        
        print('Commenting on pull requests')
        self.comment_on_pull_requests(github_api)
        

