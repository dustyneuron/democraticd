from __future__ import print_function, unicode_literals

from democraticd.config import parse_cli_config
from democraticd.utils import get_os_id_str, drop_privs_temp, gain_privs

import json
import sys
import os
import subprocess

class Installer(object):
    def __init__(self):
        self.log('Installer() starting...')
        
        self.config, args = parse_cli_config()
                
        self.log(get_os_id_str())
        self.log('Dropping privileges (reversible)... ')
        drop_privs_temp(self.config)
        self.log(get_os_id_str())
        
        data = ''
        for line in sys.stdin:
            data += line
        debs_dict = json.loads(data)
        for repo, debs in debs_dict.items():
            for d in debs:
                self.log('deb to install: ' + repo + '/' + d)

        self.log(get_os_id_str())
        self.log('Gaining privileges...')
        gain_privs(self.config)
        self.log(get_os_id_str())
        
        for repo, debs in debs_dict.items():
            for d in debs:
                self.run(['dpkg', '-i', d])
                
        self.run(['apt-get', '-f', 'check'])
        
        self.log('Installer() finished')
        
    def run(self, args):
        cmd = ' '.join(args)
        self.log('run: ' + cmd)
        r = subprocess.call(args, stderr=sys.stderr, stdout=sys.stderr)
        if r != 0:
            raise Exception('"' + cmd + '" returned ' + str(r))

    def log(self, s):
        sys.stderr.write(s + '\n')

    

def start():
    Installer()
    
if __name__ == '__main__':
    start()
