import democraticd.config

import time
import sys
import tempfile
import os
import os.path
import subprocess
import functools
import shutil
import re

def increment_version(v):
    # assume version string ends in a number, and increment that
    r = re.match('(?P<first>.*[^0-9])(?P<last>[0-9]+)$', v)
    return r.group('first') + str(int(r.group('last')) + 1)


class Builder:
    def __init__(self):
        pass

    def run(self, args):
        cmd = functools.reduce(lambda acc, x: acc + ' ' + x, args)
        print('run: ' + cmd)
        r = subprocess.call(args, stderr=sys.stderr, stdout=sys.stdout)
        if r != 0:
            raise Exception('"' + cmd + '" returned ' + str(r))
            
    def get(self, args):
        cmd = functools.reduce(lambda acc, x: acc + ' ' + x, args)
        print('get: ' + cmd)
        r = subprocess.check_output(args, stderr=sys.stderr)
        return r.decode()
            
    def build(self, package, issue_id):
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
            
        github_config = config.get_github_config()
            
        self.working_dir = tempfile.mkdtemp()
        print('Working directory is ' + self.working_dir)
        os.chdir(self.working_dir)
        
        try:
            # Use https to use .git-credentials
            self.run(['git', 'clone', 'https://github.com/' + github_config['username'] + '/' + package + '.git', package])
            os.chdir(os.path.join(self.working_dir, package))
            last_commit = self.get(['git', 'log', '-n', '1', '--pretty=format:%H']).strip()
            last_version = self.get(['git', 'tag', '--contains', last_commit]).strip()[len('debian/'):]
            
            self.run(['git', 'fetch', pr.repo_git_url, pr.ref + ':refs/remotes/' + pr.username + '/' + pr.ref])
            self.run(['git', 'merge', pr.sha])
            
            new_version = increment_version(last_version)
            
            self.run(['git-dch', '--since', last_commit, '--meta', '--commit', '-N', new_version])
            self.run(['git', 'tag', 'debian/' + new_version])
            
            self.run(['git', 'push', 'origin', '--tags'])
            self.run(['git', 'push', 'origin'])
            
            self.run(['dpkg-buildpackage', '-us', '-uc', '-b'])
        except:
            raise
        finally:        
            os.chdir(self.working_dir)
            shutil.rmtree(package)
        
        print('Built package(s) OK in ' + self.working_dir)
        

def build(package, issue_id):
    Builder().build(package, issue_id)
    
if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])


