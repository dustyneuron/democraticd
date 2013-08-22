import democraticd.config

import time
import sys
import tempfile
import os
import os.path
import subprocess
import functools

def run(args):
    cmd = functools.reduce(lambda acc, x: acc + ' ' + x, args)
    print('run: ' + cmd)
    r = subprocess.call(args, stderr=sys.stderr, stdout=sys.stdout)
    if r != 0:
        raise Exception('"' + cmd + '" returned ' + str(r))

def build(package, issue_id):
    print('build started (' + package + ', ' + issue_id + ')')
    
    config = democraticd.config.Config()
    pr_list = config.read_pull_requests(package)
    found_pr = None
    for pr in pr_list:
        if (pr.state == pr.state_idx('BUILDING')) and (pr.issue_id == int(issue_id)):
            found_pr = pr
            break
    pr = found_pr
    if not pr:
        raise Exception('No matching pull request found')
        
    working_dir = tempfile.mkdtemp()
    print('Working directory is ' + working_dir)
    os.chdir(working_dir)
    
    run(['git', 'clone', pr.repo_git_url, package])
    os.chdir(os.path.join(working_dir, package))
    run(['git', 'checkout', pr.ref])
    run(['git', 'checkout', pr.sha])
    #run(['git-dch'])
    run(['dpkg-buildpackage', '-us', '-uc', '-b'])
    
    time.sleep(5)
    
    
    print('build finished')
    
if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])


