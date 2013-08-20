import demod.config
from . import pullrequest

    
def daemon_loop(config, hosted_git):
    while True:
        print('Starting daemon loop')
        repo_dict = {}
        for repo in config.get_repo_set():
            print('Reading saved pull requests for "' + str(repo) + '"')
            repo_dict[repo] = config.read_pull_requests(repo, PullRequest)

        print('Getting new pull request notifications from GitHub API')
        new_repo_dict = pullrequest.get_new_pull_requests(config, hosted_git)
        
        for repo in repo_dict.keys():
            if repo in new_repo_dict:
                repo_dict[repo] = pullrequest.update_pull_request_list(repo_dict[repo], new_repo_dict[repo])
                
        print('Commenting on pull requests')
        pullrequest.comment_on_pull_requests(hosted_git, repo_dict)
        
        for (repo, pr_list) in repo_dict.items():
            print('Saving pull requests for "' + str(repo) + '"')
            config.write_pull_requests(repo, pr_list)

        
def go():
    config = demod.config.Config()
    hosted_git = config.create_hosted_git()
    daemon_loop(config, hosted_git)




from gevent.server import StreamServer

server = None

def echo(socket, address):
    print ('New connection from %s:%s' % address)
    socket.sendall('Welcome to the echo server! Type quit to exit.\r\n')
    fileobj = socket.makefile()
    while True:
        line = fileobj.readline()
        if not line:
            print ("client disconnected")
            break
        if line.decode().strip().lower() == 'quit':
            print ("client told server to quit")
            server.stop()
            # server.stop doesn't yield so next statement will execute
            return
        fileobj.write(line)
        fileobj.flush()
        print ("echoed back %r" % line)


server = StreamServer(('localhost', 9999), echo)
# to start the server asynchronously, use its start() method;
# we use blocking serve_forever() here because we have no other jobs
print('Starting echo server on port 9999')
server.serve_forever()



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



