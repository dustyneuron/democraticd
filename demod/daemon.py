import demod.config
import demod.build
from . import pullrequest

import gevent
import gevent.server
import gevent.event
import gevent.subprocess
import gevent.socket
import gevent.queue

import functools
import sys
import os.path
import sysconfig
    
class DemoDaemon:
    def __init__(self):
        self.python = 'python' + sysconfig.get_python_version()[0]
        self.module_dir = '.'
        if sys.argv[0]:
            self.module_dir = os.path.join(os.path.dirname(sys.argv[0]), '..')
        self.module_dir = os.path.abspath(self.module_dir)
        
        self.quit_event = gevent.event.Event()
        self.config = demod.config.Config()
        self.hosted_git = self.config.create_hosted_git(self.quit_event)

        self.server = gevent.server.StreamServer(('localhost', 9999), lambda sock, addr: DemoDaemon.command_server(self, sock, addr))
        
        self.repo_dict = {}
        
        self.build_greenlet = None
        
        self.build_queue = gevent.queue.JoinableQueue()
        
    def start(self):
        print('Starting server on port 9999')
        self.server.start()
        
        gevent.Greenlet.spawn(DemoDaemon.start_builds, self)
        
        # Queue any builds that didn't get run last time
        for repo in self.config.get_repo_set():
            self.repo_dict[repo] = self.config.read_pull_requests(repo, pullrequest.PullRequest)
            for pr in self.repo_dict[repo]:
                if pr.state == pr.state_idx('APPROVED'):
                    self.build_queue.put((pr.repo, pr.key()))
        
        # main GitHub loop, synchronous so we stay within rate limits
        while not self.quit_event.is_set():
            self.do_github_actions()
            
        print('Shutdown: waiting for all pending builds to have started')
        self.build_queue.join()
            
        print('Shutdown: waiting for current build to stop')
        if self.build_greenlet and (not self.build_greenlet.ready()):
            self.build_greenlet.join()
        
        print('Shutdown complete')

    def save_pull_requests(self, single_repo=None):
        print('Saving pull requests')
        if single_repo:
            self.config.write_pull_requests(single_repo, self.repo_dict[single_repo])
        else:
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
        
    def _proc_build(self, cmd, pr):
        gevent.subprocess.call(cmd, cwd=self.module_dir)
        print('build subprocess.call returned')
        # pr.set_state(built)?
        self.build_greenlet.kill()
        raise Exception('this code should never be called')
        
    def start_builds(self):
        while True:
            (repo, key) = self.build_queue.get()
            
            if self.build_greenlet and (not self.build_greenlet.ready()):
                print('Trying to spawn new builder, waiting for current one to finish')
                self.build_greenlet.join()
            
            idx = pullrequest.find_pull_request_idx(self.repo_dict[repo], key)
            pr = self.repo_dict[repo][idx]
            
            cmd = [
                self.python,
                '-m',
                'demod.build',
                str(pr.repo),
                str(pr.issue_id)
                ]
                
            pr.set_state('BUILDING')
            self.save_pull_requests(pr.repo)
            
            self.build_greenlet = gevent.Greenlet.spawn(DemoDaemon._proc_build, self, cmd, pr)
            print('Spawned builder')
            
            self.build_queue.task_done()
            
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
                socket.shutdown(gevent.socket.SHUT_RDWR)
                return
                
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
                
                if self.build_greenlet and (not self.build_greenlet.ready()):
                    fileobj.write(('Error - already merging a pull request\n').encode())
                    found_pr = None
                
                if found_pr:
                    fileobj.write(('PULL REQUEST APPROVED\n').encode())
                    fileobj.write(found_pr.pretty_str().encode())
                    
                    found_pr.set_state('APPROVED')
                    self.save_pull_requests(found_pr.repo)
                    self.build_queue.put((found_pr.repo, found_pr.key()))
                    
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



