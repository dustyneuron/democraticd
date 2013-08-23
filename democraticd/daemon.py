import democraticd.config
import democraticd.build
import democraticd.pr_db
from democraticd.utils import DebugLevel

import gevent
import gevent.server
import gevent.event
import gevent.subprocess
import gevent.socket
import gevent.queue

import functools
import sys
import os.path
import re
    
class DemocraticDaemon:
    def __init__(self, debug_level=DebugLevel.ESSENTIAL, mark_read=True,
            make_comments=True, run_builds=True, install_packages=True):
                
        self.debug_level = debug_level
        self.run_builds = run_builds
        self.install_packages = install_packages
        
        self.quit_event = gevent.event.Event()
        
        self.config = democraticd.config.Config(debug_level=self.debug_level, mark_read = mark_read)
        
        self.github_api = self.config.create_github_api(self.quit_event, make_comments)

        self.server = gevent.server.StreamServer(
            ('localhost', self.config.port),
            lambda sock, addr: self.command_server(sock, addr)
            )
        
        self.pr_db  = democraticd.pr_db.PullRequestDB(self.config)
        
        self.build_greenlet = None
        self.build_queue = gevent.queue.JoinableQueue()
        
    def log(self, *args):
        self.config.log(*args)
        
    def start(self):
        print('Starting server on port ' + str(self.config.port))
        self.server.start()
        
        gevent.Greenlet.spawn(self.start_builds)
        
        # Queue any builds that didn't get run last time
        for repo in self.config.get_repo_set():
            self.pr_db.read_pull_requests(repo)
            for pr in self.pr_db.pull_requests(repo):
                if pr.state == pr.state_idx('APPROVED'):
                    self.build_queue.put((pr.repo, pr.key()))
        
        # main GitHub loop, synchronous so we stay within rate limits
        while not self.quit_event.is_set():
            self.pr_db.do_github_actions(self.github_api)
            
        print('Shutdown: waiting for all pending builds to have started')
        self.build_queue.join()
            
        print('Shutdown: waiting for current build to stop')
        if self.build_greenlet and (not self.build_greenlet.ready()):
            self.build_greenlet.join()
        
        print('Shutdown complete')
        
        
    def build_thread(self, pr):
        r = self.config.run_build(pr, gevent.subprocess)
        print('build subprocess.call returned ' + str(r))
        if r == 0:
            pr.set_state('INSTALLING')
            self.pr_db.write_pull_requests(pr.repo)
            if self.install_packages:
                r = self.config.run_install(pr, gevent.subprocess)
                if r == 0:
                    pr.set_state('DONE')
                    self.pr_db.write_pull_requests(pr.repo)
        
        self.build_greenlet.kill()
        raise Exception('this code should never be called')
        
    def start_builds(self):
        while True:
            (repo, key) = self.build_queue.get()
            
            if self.build_greenlet and (not self.build_greenlet.ready()):
                print('Trying to spawn new builder, waiting for current one to finish')
                self.build_greenlet.join()
            
            pr = self.pr_db.find_pull_request(repo, key)
            
            pr.set_state('BUILDING')
            self.pr_db.write_pull_requests(pr.repo)
            
            if self.run_builds:
                self.build_greenlet = gevent.Greenlet.spawn(self.build_thread, pr)
                print('Spawned builder')
            else:
                print('Would have spawned builder, but run_builds=False')
            
            self.build_queue.task_done()
            
    def command_server(self, socket, address):
        print ('New connection from %s:%s' % address)
        socket.sendall('Welcome to the Democratic Daemon server!\n')
        help_message = 'Commands are "stop", "list" and "approve"\n'
        socket.sendall(help_message)
        fileobj = socket.makefile()
        while True:
            try:
                line = fileobj.readline()                    
                if not line:
                    print ("client disconnected")
                    return
                    
                command = line.decode().strip().lower()
                single_cmd = False
                if command.startswith('$'):
                    command = command[1:]
                    single_cmd = True
                    print('Received single command ' + repr(command))
                    
                if command == 'stop':
                    print ("client told server to stop")
                    fileobj.write(('STOPPING SERVER\n').encode())
                    fileobj.flush()
                    self.quit_event.set()
                    self.server.stop()
                    socket.shutdown(gevent.socket.SHUT_RDWR)
                    return
                    
                elif command == 'list':
                    empty = True
                    for repo in self.pr_db.repos():
                        for pr in self.pr_db.pull_requests(repo):
                            fileobj.write(pr.pretty_str().encode())
                            empty = False
                    if empty:
                        fileobj.write('No pull requests\n'.encode())

                elif command.startswith('approve'):
                    r = re.match('approve\s+(?P<repo>\S+)\s+(?P<issue_id>\d+)\s*$', command)
                    issue_id = None
                    repo = None
                    if r:
                        repo = r.group('repo')
                        try:
                            issue_id = int(r.group('issue_id'))
                        except Exception as e:
                            fileobj.write(('error parsing integer issue number\n' + str(e) + '\n').encode())
                    else:
                        fileobj.write(('error - usage is "approve [repo] [issue_id]"\n').encode())
                                            
                    found_pr = None
                    if issue_id and repo and repo in self.pr_db.repos():
                        for pr in self.pr_db.pull_requests(repo):
                            if pr.state == pr.state_idx('COMMENTED'):
                                if pr.issue_id == issue_id:
                                    found_pr = pr
                                    break
                                    
                    if found_pr:
                        fileobj.write(('PULL REQUEST APPROVED\n').encode())
                        fileobj.write(found_pr.pretty_str().encode())
                        
                        found_pr.set_state('APPROVED')
                        self.pr_db.write_pull_requests(found_pr.repo)
                        self.build_queue.put((found_pr.repo, found_pr.key()))
                        
                    else:
                        fileobj.write(('No pull request "' + str(repo) + '/issue #' + str(issue_id) + '" ready for merging\n').encode())
                    
                else:
                    fileobj.write(('Unknown command "' + command + '"\n').encode())
                    fileobj.write(help_message.encode())
                    
                fileobj.flush()
                if single_cmd:
                    socket.shutdown(gevent.socket.SHUT_RDWR)
                    return
                    
            except Exception as e:
                print(e)
                try:
                    socket.shutdown(gevent.socket.SHUT_RDWR)
                except Exception as e2:
                    print(e2)
                return


def start():
    DemocraticDaemon().start()
    
def debug(**keywords):
    args = {}
    args.update(debug_level=DebugLevel.DEBUG, mark_read=False, make_comments=False,
        run_builds=False, install_packages=False)
    args.update(keywords)
    DemocraticDaemon(**args).start()

if __name__ == "__main__":
    start()
