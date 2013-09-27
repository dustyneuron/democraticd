from __future__ import print_function, unicode_literals

from democraticd import github_api
from democraticd.utils import DebugLevel
from democraticd.pullrequest import prs_to_json

import os
import os.path
import json
import sysconfig
import sys
import datetime

# TODO: file locking for safe IPC e.g. with build system
# Sqlite would work, but a schema-less solution is best
# python-lockfile? python-zc.lockfile? lockfile-progs?
# Cross-platform is good, python3 support mandatory :P
#
# OR: just pass the PR data via pipes etc to build/voting systems
# - They don't need write access

class Config(object):
    def __init__(self, dev_install, debug_level=None, mark_read=None):
        if dev_install:
            self.conf_dir = os.path.expanduser('~/.democraticd/')
            default_log = os.path.join(self.conf_dir, 'democraticd.log')
        else:
            self.conf_dir = '/etc/democraticd/'
            default_log = '/var/log/democraticd.log'
        
        self.packages_dir = os.path.join(self.conf_dir, 'packages')
        self.debs_dir = os.path.join(self.conf_dir, 'debs')
        self.pull_requests_dir = os.path.join(self.conf_dir, 'pull-requests')
        self.json_extension = '.json'
        
        filename = os.path.join(self.conf_dir, 'config.json')
        if not os.path.exists(filename):
            raise Exception('Not installed properly - ' + filename + ' does not exist')
        with open(filename, 'rt') as f:
            file_values = json.loads(f.read() or '{}')
        
        self.port = file_values.get('port', 9999)
        
        if debug_level == None:
            debug_level = file_values.get('debug_level', DebugLevel.ESSENTIAL)
        self.debug_level = debug_level
            
        if mark_read == None:
            mark_read = file_values.get('mark_read', True)
        self.mark_read = mark_read
        
        self.uid = file_values.get('uid', 1000)
        self.gid = file_values.get('gid', 1000)
        
        self.log_filename = file_values.get('log_file', default_log)

        self.python = 'python' + sysconfig.get_python_version()[0]
        self.module_dir = '.'
        if sys.argv[0]:
            self.module_dir = os.path.join(os.path.dirname(sys.argv[0]), '..')
        self.module_dir = os.path.abspath(self.module_dir)
        
        self.log('Loaded democraticd config OK')
                
    def create_missing_config(self):
        if not os.path.exists(self.conf_dir):
            raise Exception('Not installed properly - config dir ' + self.conf_dir + ' does not exist')
        if not os.path.exists(self.packages_dir):
            os.makedirs(self.packages_dir)
        if not os.path.exists(self.debs_dir):
            os.makedirs(self.debs_dir)
        if not os.path.exists(self.pull_requests_dir):
            os.makedirs(self.pull_requests_dir)
        
        
    def run_script(self, module_name, input_string, subprocess):
        cmd = [self.python, '-m', 'democraticd.' + module_name]
        self.log('Popen ' + ' '.join(cmd))
        p = subprocess.Popen(cmd, cwd=self.module_dir, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr)
        data, _ = p.communicate(input_string.encode())
        #p.stdin.write(input_string.encode())
        #p.stdin.close()
        #p.wait()
        return p.returncode, data
                
    def log(self, data, debug_level=DebugLevel.ESSENTIAL):
        if self.debug_level >= debug_level:
            print(str(datetime.datetime.now()) + ': ' + data)
            sys.stdout.flush()
            
    def add_package(self, package_name, module_names=[]):
        filename = os.path.join(self.packages_dir, package_name + self.json_extension)
        data = {'modules' : module_names}
        with open(filename, 'wt') as f:
            f.write(json.dumps(data, sort_keys=True, indent=4))
        filename = self.get_pull_requests_filename(package_name)
        with open(filename, 'wt') as f:
            f.write(json.dumps([], sort_keys=True, indent=4))
            
    def del_package(self, package_name):
        filename = os.path.join(self.packages_dir, package_name + self.json_extension)
        os.remove(filename)
        
    def get_package_set(self):
        package_names = set([])
        files = os.listdir(self.packages_dir)
        for f in files:
            length = len(f) - len(self.json_extension)
            if (length > 0):
                package_names.add(f[0:length])
        return package_names
        
    def get_package_data(self, package_name):
        filename = os.path.join(self.packages_dir, package_name + self.json_extension)
        with open(filename, 'rt') as f:
            data = json.loads(f.read())
        return data

    def get_package_module_set(self, package_name):
        return set(self.get_package_data(package_name)['modules'])
                
    def get_module_set(self):
        module_set = set([])
        package_names = self.get_package_set()
        for p in package_names:
            module_set = module_set.union(self.get_package_module_set(p))
        return module_set
        
    def get_repo_set(self):
        return self.get_package_set().union(self.get_module_set())
        
    def get_github_config(self):
        filename = os.path.join(self.conf_dir, "github_api.json")
        with open(filename, 'rt') as f:
            config = json.loads(f.read())
        return config
        
    def create_github_api(self, quit_event, make_comments=True):
        config = self.get_github_config()
        return github_api.GitHubAPI(config['username'], config['password'], quit_event, self.log, make_comments)

    def get_pull_requests_filename(self, repo):
        return os.path.join(self.pull_requests_dir, repo + self.json_extension)

    def get_deb_directory(self, repo):
        d = os.path.join(self.debs_dir, repo + '/')
        if not os.path.exists(d):
            os.makedirs(d)
        return d
        

