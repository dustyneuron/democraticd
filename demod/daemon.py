import demod.config
from . import pullrequest

import gevent
import gevent.server
import gevent.event

import functools
    
class DemoDaemon:
    def __init__(self):
        self.quit_event = gevent.event.Event()
        self.config = demod.config.Config()
        self.hosted_git = self.config.create_hosted_git(self.quit_event)

        self.server = gevent.server.StreamServer(('localhost', 9999), lambda sock, addr: DemoDaemon.command_server(self, sock, addr))
        
        self.repo_dict = {}
        
    def start(self):
        print('Starting server on port 9999')
        self.server.start()
        
        while not self.quit_event.is_set():
            self.do_github_actions()

    def save_pull_requests(self):
        print('Saving all pull requests')
        for (repo, pr_list) in self.repo_dict.items():
            self.config.write_pull_requests(repo, pr_list)

    def do_github_actions(self):
        print('At top of daemon loop')
        for repo in self.config.get_repo_set():
            print('Reading saved pull requests for "' + str(repo) + '"')
            self.repo_dict[repo] = self.config.read_pull_requests(repo, pullrequest.PullRequest)

        print('Getting new pull request notifications from GitHub API')
        new_repo_dict = pullrequest.get_new_pull_requests(self.config, self.hosted_git)
        if new_repo_dict:
            for repo in self.repo_dict.keys():
                if repo in new_repo_dict:
                    self.repo_dict[repo] = pullrequest.update_pull_request_list(self.repo_dict[repo], new_repo_dict[repo])
        self.save_pull_requests()
                    
        print('Filling any pull requests if needed')
        pullrequest.fill_pull_requests(self.hosted_git, self.repo_dict)
        self.save_pull_requests()
                
        print('Commenting on pull requests')
        pullrequest.comment_on_pull_requests(self.hosted_git, self.repo_dict)
        self.save_pull_requests()
                    
            
    def command_server(self, socket, address):
        print ('New connection from %s:%s' % address)
        socket.sendall('Welcome to the Democratic Daemon server!\n')
        help_message = 'Commands are "stop", "list" and "approve"\n'
        socket.sendall(help_message)
        fileobj = socket.makefile()
        while True:
            line = fileobj.readline()
            if not line:
                print ("client disconnected")
                break
                
            command = line.decode().strip().lower()
            if command == 'stop':
                print ("client told server to stop")
                fileobj.write(('STOPPING SERVER\n').encode())
                self.quit_event.set()
                self.server.stop()
                break
            elif command == 'list':
                for (repo, pr_list) in self.repo_dict.items():
                    for pr in pr_list:
                        fileobj.write(pr.pretty_str().encode())

            elif command.startswith('approve'):
                issue_id = None
                try:
                    issue_id = int(command[len('approve '):])
                except Exception as e:
                    fileobj.write(('error parsing integer issue number\n' + str(e) + '\n').encode())
                    
                found_pr = None
                if issue_id:
                    for pr in functools.reduce(lambda acc, x: acc + x, self.repo_dict.values()):
                        if pr.state == pr.state_idx('COMMENTED'):
                            if pr.issue_id == issue_id:
                                found_pr = pr
                                break
                            
                if found_pr:
                    fileobj.write(('MERGING PULL REQUEST\n').encode())
                    fileobj.write(found_pr.pretty_str().encode())
                else:
                    fileobj.write(('No pull request with id #' + str(issue_id) + ' ready for merging\n').encode())
                
            else:
                fileobj.write(('Unknown command "' + command + '"\n').encode())
                fileobj.write(help_message.encode())
                
            fileobj.flush()



if __name__ == '__main__':
    DemoDaemon().start()


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



