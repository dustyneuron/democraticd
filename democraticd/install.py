from __future__ import print_function, unicode_literals

import json

class Installer:
    def __init__(self):
        data = ''
        for line in sys.stdin:
            data += line
        debs_dict = json.loads(data)
        for repo, debs in debs_dict:
            for d in debs:
            self.log('deb to install: ' + repo + '/' + d)

    def log(self, s):
        sys.stdout.write(s + '\n')

    

def start():
    Installer()
    
if __name__ == '__main__':
    start()
