from __future__ import print_function, unicode_literals

import gevent
import gevent.socket as socket
import gevent.event
from gevent.fileobject import FileObject

from democraticd.config import parse_cli_config

import sys
import re

def start():    
    dev_install = False
    single_cmd = None
    
    config, args = parse_cli_config()
    if len(args) > 0:
        single_cmd = b'$' + ' '.join(args).strip().encode() + b'\n'
    
    if not single_cmd:
        print('Connecting to the democratic daemon on port ' + str(config.port) + '... ', end='')
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', config.port))
    except:
        print('')
        raise
    if not single_cmd:
        print('ok')
    
    socket_reader = s.makefile()
    greet = b'' + socket_reader.readline() + socket_reader.readline()
    if not single_cmd:
        print(greet.decode(), end='')

    do_quit = gevent.event.Event()
    gevent.Greenlet.spawn(input_loop, s, do_quit, single_cmd)
    gevent.Greenlet.spawn(output_loop, s, do_quit, single_cmd)
    do_quit.wait()
    s.close()
    
def input_loop(s, do_quit, single_cmd):
    if not single_cmd:
        print('Type quit or a blank line to close the connection')
        sys.stdout.flush()
        file_in = FileObject(sys.stdin)
        
    while not do_quit.is_set():
        sys.stdout.flush()
        if single_cmd:
            line = single_cmd
        else:
            line = file_in.readline()
            
        if not line or not line.decode().strip() or re.match('quit$', line.decode().strip().lower()):
            print('bye!')
            do_quit.set()
            break
            
        s.sendall(line)
        
        if single_cmd:
            break

def output_loop(s, do_quit, single_cmd):
    socket_reader = s.makefile()
    while not do_quit.is_set():
        line = socket_reader.readline()
        if not line:
            if not single_cmd:
                print('daemon closed the connection')
            do_quit.set()
            break
            
        print(line.decode(), end='')
        sys.stdout.flush()
        
if __name__ == "__main__":
    start()
