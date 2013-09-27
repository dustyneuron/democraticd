from __future__ import print_function, unicode_literals

import json
import sys

class Installer:
    def __init__(self):
        self.log('Installer() starting...')
        data = ''
        for line in sys.stdin:
            data += line
        debs_dict = json.loads(data)
        for repo, debs in debs_dict.items():
            for d in debs:
                self.log('deb to install: ' + repo + '/' + d)
                
        self.log('Installer() finished')

    def log(self, s):
        sys.stderr.write(s + '\n')

    

def start():
    Installer()
    
if __name__ == '__main__':
    start()
