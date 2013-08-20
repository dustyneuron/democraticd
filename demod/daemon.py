import demod.config
from . import pullrequest

import gevent
import gevent.server
import gevent.event
    
def do_github_actions(config, hosted_git):
    print('At top of daemon loop')
    repo_dict = {}
    for repo in config.get_repo_set():
        print('Reading saved pull requests for "' + str(repo) + '"')
        repo_dict[repo] = config.read_pull_requests(repo, pullrequest.PullRequest)

    print('Getting new pull request notifications from GitHub API')
    new_repo_dict = pullrequest.get_new_pull_requests(config, hosted_git)
    if new_repo_dict:
        for repo in repo_dict.keys():
            if repo in new_repo_dict:
                repo_dict[repo] = pullrequest.update_pull_request_list(repo_dict[repo], new_repo_dict[repo])
            
    print('Commenting on pull requests')
    pullrequest.comment_on_pull_requests(hosted_git, repo_dict)
    
    for (repo, pr_list) in repo_dict.items():
        print('Saving pull requests for "' + str(repo) + '"')
        config.write_pull_requests(repo, pr_list)
        

def command_server(socket, address):
    print ('New connection from %s:%s' % address)
    socket.sendall('Welcome to the Democratic Daemon server!\r\n')
    help_message = 'Commands are "quit", "list" and "approve"\r\n'
    socket.sendall(help_message)
    fileobj = socket.makefile()
    while True:
        line = fileobj.readline()
        if not line:
            print ("client disconnected")
            break
            
        command = line.decode().strip().lower()
        if command == 'quit':
            print ("client told server to quit")
            quit_event.set()
            server.stop()
            break
        elif command == 'list':
            pass
        elif command == 'approve':
            pass
        else:
            fileobj.write(('Unknown command "' + command + '"\r\n').encode())
            fileobj.write(help_message.encode())
            
        fileobj.write(line)
        fileobj.flush()
        print ("echoed back %r" % line)


if __name__ == '__main__':
    quit_event = gevent.event.Event()
    server = gevent.server.StreamServer(('localhost', 9999), command_server)
    print('Starting server on port 9999')
    server.start()
    
    config = demod.config.Config()
    hosted_git = config.create_hosted_git(quit_event)
    
    while not quit_event.is_set():
        do_github_actions(config, hosted_git)


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



