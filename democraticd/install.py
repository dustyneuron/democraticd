from __future__ import print_function, unicode_literals

from democraticd.config import parse_cli_config

import json
import sys
import os
import subprocess

class Installer(object):
    def __init__(self):
        self.log('Installer() starting...')
        
        self.config, args = parse_cli_config()
        
        data = ''
        for line in sys.stdin:
            data += line
        debs_dict = json.loads(data)
        for repo, debs in debs_dict.items():
            for d in debs:
                self.log('deb to install: ' + repo + '/' + d)

        self.log_ids()
        self.log('Gaining privileges...')
        os.setegid(self.config.gid)
        os.seteuid(self.config.uid)
        self.log_ids()
        
        for repo, debs in debs_dict.items():
            for d in debs:
                self.run(['dpkg', '-i', d])
                
        self.run(['apt-get', '-f', 'check'])
        
        self.log('Dropping privileges...')
        os.setegid(self.config.egid)
        os.seteuid(self.config.euid)
        self.log_ids()

        self.log('Installer() finished')
        
    def run(self, args):
        cmd = ' '.join(args)
        self.log('run: ' + cmd)
        r = subprocess.call(args, stderr=sys.stderr, stdout=sys.stderr)
        if r != 0:
            raise Exception('"' + cmd + '" returned ' + str(r))

    def log_ids(self):
        ids = [os.getuid(), os.getgid(), os.geteuid(), os.getegid()]
        self.log('uid, gid, euid, egid = ' + ', '.join([str(x) for x in ids]))

    def log(self, s):
        sys.stderr.write(s + '\n')

    

def start():
    Installer()
    
if __name__ == '__main__':
    start()
