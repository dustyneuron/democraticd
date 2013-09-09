from democraticd import github_api
from democraticd.utils import DebugLevel

import os
import json
import sysconfig
import sys

# TODO: file locking for safe IPC e.g. with build system
# Sqlite would work, but a schema-less solution is best
# python-lockfile? python-zc.lockfile? lockfile-progs?
# Cross-platform is good, python3 support mandatory :P
#
# OR: just pass the PR data via pipes etc to build/voting systems
# - They don't need write access

class Config:
    def __init__(self, debug_level=DebugLevel.ESSENTIAL, mark_read = True, conf_dir = "/home/tom/.demod/"):
        self.conf_dir = conf_dir
        self.packages_dir = os.path.join(self.conf_dir, "packages")
        self.debs_dir = os.path.join(self.conf_dir, "debs")
        self.pull_requests_dir = os.path.join(self.conf_dir, "pull-requests")
        self.json_extension = ".json"
        self.port = 9999
        self.debug_level = debug_level
        self.mark_read = mark_read
        
        os.makedirs(self.packages_dir, exist_ok=True)
        os.makedirs(self.debs_dir, exist_ok=True)
        os.makedirs(self.pull_requests_dir, exist_ok=True)
        
        self.python = 'python' + sysconfig.get_python_version()[0]
        self.module_dir = '.'
        if sys.argv[0]:
            self.module_dir = os.path.join(os.path.dirname(sys.argv[0]), '..')
        self.module_dir = os.path.abspath(self.module_dir)
        
    def run_build(self, pr, subprocess):
        cmd = [self.python, '-m', 'democraticd.build']
        self.log('Popen ' + ' '.join(cmd))
        p = subprocess.Popen(cmd, cwd=self.module_dir, stdin=subprocess.PIPE)
        pr.write_to_file(p.stdin)
        p.stdin.close()
        return p.wait()
        
    def run_install(self, pr, subprocess):
        print('TODO: implement deb install')
        return 0
        
    def log(self, data, debug_level=DebugLevel.ESSENTIAL):
        if self.debug_level >= debug_level:
            print(data)
            
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
        os.makedirs(d, exist_ok=True)
        return d
        

