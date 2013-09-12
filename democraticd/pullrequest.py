import json

def prs_to_json(pr_list):
    dict_list = [pr.to_dict() for pr in pr_list]
    return json.dumps(dict_list, sort_keys=True, indent=4) + '\n'
    
def prs_from_json(data):
    dict_list = json.loads(data)
    return [PullRequest.create_from_dict(dic) for dic in dict_list]
    

class PullRequest:
    states = {
        0: 'EMPTY',
        1: 'NEW',
        2: 'FILLED',
        3: 'COMMENTED',
        4: 'APPROVED',
        5: 'BUILDING',
        6: 'INSTALLING',
        7: 'DONE'
        }
            
    def __init__(self, data=None):
        self.needs_update = False
        self.reset_voting = False
        if data:
            self.repo = data['repository']['name']
            self.title = data['subject']['title']
            self.pull_api_url = data['subject']['url']
            self.repo_type = None
            self.set_state('NEW')
        else:
            self.set_state('EMPTY')
            
    @classmethod
    def create_from_dict(cls, dic):
        pr = cls()
        for (k, v) in dic.items():
            pr.__dict__[k] = v
        return pr
    
    def to_dict(self):
        return vars(self)
    
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
        
    def notify_update(self):
        self.needs_update = True
        
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
        self.html_url = data['_links']['html']['href']
        self.set_state('FILLED')
        
    def update(self, found_pr_data, notify_voting_func):
        self.needs_update = False
        notify_voting = False
        if found_pr_data:
            if self.state < self.state_idx('FILLED'):
                self.fill(found_pr_data)
                
            if found_pr_data['state'] != 'open':
                self.set_state('DONE')
                self.error = 'Pull request marked as ' + repr(found_pr_data['state'])
                notify_voting = True
                
            if found_pr_data['head']['sha'] != self.sha:
                # The requester has pushed more commits to the PR
                self.sha = found_pr_data['head']['sha']
                notify_voting = True
        else:
            self.error = 'Pull request deleted whilst in state ' + self.get_state()
            self.set_state('DONE')
            notify_voting = True
            
        if notify_voting:
            notify_voting_func(self)
        
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

                                
