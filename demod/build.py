import time
import sys
    

def build(issue_id):
    print('build started (' + issue_id + ')')
    time.sleep(30)
    print('build finished')
    
if __name__ == '__main__':
    build(sys.argv[1])


