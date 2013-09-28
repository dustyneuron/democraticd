from __future__ import print_function, unicode_literals

import datetime
import sys
import os

def iso_8601(dt):
    if dt.tzinfo:
        #dt = dt.astimezone(tz=datetime.timezone.utc).replace(tzinfo=None)
        raise Exception('No timezone-aware conversion in utils.iso_8601 yet')
    return dt.replace(microsecond=0).isoformat() + 'Z'


class DebugLevel(object):
    ESSENTIAL = 0
    INFO = 1
    DEBUG = 2
    

def parse_cli_options():
    options = {}
    options['dev_install'] = False
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        if '--dev' in args:
            args.remove('--dev')
            options['dev_install'] = True
    else:
        args = []
    
    return options, args

def get_common_cli_argv():
    if '--dev' in sys.argv:
        return ['--dev']
    return []
    
def get_os_id_str():
    ids = [os.getuid(), os.getgid(), os.geteuid(), os.getegid()]
    return 'uid, gid, euid, egid = ' + ', '.join([str(x) for x in ids])

def gain_privs(config):
    os.setegid(self.config.gid)
    os.seteuid(self.config.uid)

def drop_privs_temp(config):
    os.setegid(config.egid)
    os.seteuid(config.euid)
    
def drop_privs_perm(config):
    gain_privs(config)
    os.setgid(config.egid)
    os.setuid(config.euid)
