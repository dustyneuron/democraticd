    
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

                                
