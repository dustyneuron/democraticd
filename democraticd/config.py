from democraticd import github_api
from democraticd import pullrequest
from democraticd.utils import DebugLevel

import os
import json

# TODO: file locking for safe IPC e.g. with build system
# Sqlite would work, but a schema-less solution is best
# python-lockfile? python-zc.lockfile? lockfile-progs?
# Cross-platform is good, python3 support mandatory :P

class Config:
    def __init__(self, debug_level=DebugLevel.ESSENTIAL):
        self.conf_dir = "/home/tom/.demod/"
        self.packages_dir = os.path.join(self.conf_dir, "packages")
        self.pull_requests_dir = os.path.join(self.conf_dir, "pull-requests")
        self.json_extension = ".json"
        self.port = 9999
        self.debug_level = debug_level
        
    def log(self, data, debug_level=DebugLevel.ESSENTIAL):
        if self.debug_level >= debug_level:
            print(data)
        
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
        
    def get_package_deb_set(self, package_name):
        return set(self.get_package_data(package_name)['deb_packages'])
        
    def get_module_set(self):
        module_set = set([])
        package_names = self.get_package_set()
        for p in package_names:
            module_set = module_set.union(self.get_package_module_set(p))
        return module_set
        
    def get_repo_set(self):
        return self.get_package_set().union(self.get_module_set())
        
    def get_github_config(self):
        with open(os.path.join(self.conf_dir, "github_api.json"), 'rt') as f:
            config = json.loads(f.read())
        return config
        
    def create_github_api(self, quit_event, make_comments=True):
        config = self.get_github_config()
        return github_api.GitHubAPI(config['username'], config['password'], quit_event, self.log, make_comments)

    def read_pull_requests(self, repo):
        filename = os.path.join(self.pull_requests_dir, repo + self.json_extension)
        pr_list = []
        with open(filename, 'rt') as f:
            data = json.loads(f.read())
        for d in data:
            pr = pullrequest.PullRequest()
            for (k, v) in d.items():
                pr.__dict__[k] = v
            pr_list.append(pr)
            
        return pr_list

    def write_pull_requests(self, repo, pr_list):
        filename = os.path.join(self.pull_requests_dir, repo + self.json_extension)
        data = []
        for pr in pr_list:
            data.append(vars(pr))
            
        with open(filename, 'wt') as f:
            f.write(json.dumps(data, sort_keys=True, indent=4))
        


