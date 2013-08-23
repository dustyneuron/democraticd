import functools
    
class PullRequest:
    states = {
        0: 'EMPTY',
        1: 'NEW',
        2: 'FILLED',
        3: 'COMMENTED',
        4: 'APPROVED',
        5: 'BUILDING',
        6: 'INSTALLING',
        }
            
    def __init__(self, data=None):
        if data:
            self.repo = data['repository']['name']
            self.title = data['subject']['title']
            self.pull_api_url = data['subject']['url']
            self.repo_type = None
            self.set_state('NEW')
        else:
            self.set_state('EMPTY')
    
    def key(self):
        return self.pull_api_url
            
    def state_idx(self, label):
        for (k, v) in self.states.items():
            if v == label:
                return k
        raise Exception('No such state ' + str(label))

    def set_state(self, label):
        self.state = self.state_idx(label)

    def get_state(self):
        return self.states[self.state]
    
    def is_more_recent_than(self, pr):
        return (self.state > pr.state)
        
    def fill(self, data):
        if data['base']['repo']['name'] != self.repo:
            raise Exception('Full pull request name does not match')
        
        self.issue_id = data['number']
        self.description = data['body']
        self.username = data['head']['repo']['owner']['login']
        self.ref = data['head']['ref']
        self.sha = data['head']['sha']
        self.base_ref = data['base']['ref']
        self.base_sha = data['base']['sha']
        self.repo_git_url = data['head']['repo']['clone_url']
        self.repo_api_url = data['head']['repo']['url']
        self.set_state('FILLED')
        
    def set_vote_url(self):
        self.vote_url = 'http://someurl.com/vote/' + self.repo + '/' + str(self.issue_id) + '/'
        
    def set_comment_log(self, data):
        self.comment_id = data['id']
        self.comment_api_url = data['url']
        self.comment_body = data['body']
        self.set_state('COMMENTED')
        
    def __str__(self):
        return self.pretty_str()
        
    def pretty_str(self):
        if self.state >= self.state_idx('FILLED'):
            s = 'Pull request "' + str(self.repo) + '/#' + str(self.issue_id) + '", state ' + self.get_state() + '\n'
            s += '\t' + self.title + '\n'
            s += '\t' + self.description + '\n'
            s += '\t' + self.pull_api_url + '\n'
            if hasattr(self, 'comment_id'):
                s += '\tComment Id #' + str(self.comment_id) + '\n'
                
        elif self.state >= self.state_idx('NEW'):
            s = 'Pull request "' + str(self.repo) + '", state ' + self.get_state() + '\n'
            s += '\t' + self.title + '\n'
            s += '\t' + self.pull_api_url + '\n'
        else:
            s = 'Pull request state EMPTY'
        return s

                
def find_pull_request_idx(pr_list, key):
    matching_prs = [idx for idx in list(range(len(pr_list))) if pr_list[idx].key() == key]
    if len(matching_prs) == 0:
        return -1
    elif len(matching_prs) == 1:
        return matching_prs[0]
    else:
        raise Exception('pr_list has multiple prs for a single key')


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


def fill_pull_requests(github_api, repo_dict):
    need_fill = False
    for pr in functools.reduce(lambda acc, x: acc + x, repo_dict.values()):
        if pr.state < pr.state_idx('FILLED'):
            need_fill = True
            break
    if not need_fill:
        return
        
    for repo in repo_dict.keys():
        list_pull_requests = github_api.list_pull_requests(repo)
        for pr in repo_dict[repo][:]:
            if pr.state < pr.state_idx('FILLED'):
                for full_pr in list_pull_requests:
                    if pr.pull_api_url == full_pr['url']:
                        pr.fill(full_pr)
                        break
            if pr.state < pr.state_idx('FILLED'):
                print('No matching full pull request for ' + str(pr) + ', deleting it')
                repo_dict[repo].remove(pr)
                


def get_new_pull_requests(config, github_api, mark_read=True):
    notifications = github_api.get_new_notifications(mark_read=mark_read)
    if not notifications:
        return {}
    
    package_set = config.get_package_set()
    module_set = config.get_module_set()
    repo_dict = create_pull_requests(notifications, package_set, module_set)
    
    return repo_dict

def update_pull_request_list(old_rp_list, new_rp_list):
    new_list = list(old_rp_list)
    for new_rp in new_rp_list:
        idx = find_pull_request_idx(old_rp_list, new_rp.key())
        if idx == -1:
            new_list.append(new_rp)
        elif new_rp.is_more_recent_than(old_rp_list[idx]):
            old_rp_list[idx] = new_rp
            
    return new_list

def comment_on_pull_requests(github_api, repo_dict):    
    for pr in functools.reduce(lambda acc, x: acc + x, repo_dict.values()):
        if pr.state == pr.state_idx('FILLED'):
            # Would interact with db at this point, the vote url needs to be live
            pr.set_vote_url()
            github_api.create_pull_request_comment(pr)

