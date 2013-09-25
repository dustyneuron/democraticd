from __future__ import print_function, unicode_literals

import democraticd.config
from democraticd.pullrequest import PullRequest, prs_from_json

import time
import sys
import tempfile
import os
import os.path
import subprocess
import functools
import shutil
import re
import json

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
            
    def build(self, ):
        print('build started')

        data = ''
        for line in sys.stdin:
            data += line
        pr = prs_from_json(data)[0]
        for (k, v) in pr.__dict__.items():
            print('build pr > ' + str(k) + ' = ' + str(v))
        
        config = democraticd.config.Config()            
        github_config = config.get_github_config()
            
        self.working_dir = tempfile.mkdtemp()
        print('Working directory is ' + self.working_dir)
        os.chdir(self.working_dir)
        
        try:
            # Use https to use .git-credentials
            self.run(['git', 'clone', 'https://github.com/' + github_config['username'] + '/' + pr.repo + '.git', pr.repo])
            os.chdir(os.path.join(self.working_dir, pr.repo))
            last_commit = self.get(['git', 'log', '-n', '1', '--pretty=format:%H']).strip()
            
            self.run(['git', 'fetch', pr.repo_git_url, pr.ref + ':refs/remotes/' + pr.username + '/' + pr.ref])
            self.run(['git', 'merge', pr.sha])
            
            #last_version = self.get(['git', 'tag', '--contains', last_commit]).strip()[len('debian/'):]
            last_version = self.get(['git', 'tag', '--contains', pr.sha]).strip()[len('debian/'):]
            new_version = increment_version(last_version)
            
            self.run(['git-dch', '--since', last_commit, '--meta', '--commit', '-N', new_version])
            self.run(['git', 'tag', 'debian/' + new_version])
            
            self.run(['git', 'push', 'origin', '--tags'])
            self.run(['git', 'push', 'origin'])
            
            self.run(['dpkg-buildpackage', '-us', '-uc', '-b'])
        except:
            os.chdir('/')
            shutil.rmtree(self.working_dir)
            raise
          
        os.chdir(self.working_dir)
        shutil.rmtree(pr.repo)
        print('Built package(s) OK in ' + self.working_dir)
        files = os.listdir(self.working_dir)
        for f in files:
            if re.match('.*\.deb$', f):
                src = os.path.join(self.working_dir, f)
                dest = os.path.join(config.get_deb_directory(pr.repo), f)
                print('Copying ' + src + ' to ' + dest)
                shutil.copy(src, dest)
                
        os.chdir('/')
        shutil.rmtree(self.working_dir)
        
def start():
    Builder().build()
    
if __name__ == '__main__':
    start()


