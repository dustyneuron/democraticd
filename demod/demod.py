#!/usr/bin/env python3.3

import os
import json
import demod.hostedgit


class DemodConfig:
    def __init__(self):
        self.conf_dir = "/home/tom/demod/debian/etc/demod/"
        self.packages_dir = os.path.join(self.conf_dir, "packages")
        self.json_extension = ".json"
        
    def get_package_set(self):
        package_names = set([])
        files = os.listdir(self.packages_dir)
        for f in files:
            length = len(f) - len(json_extension)
            if (length > 0):
                package_names.add(f[0:length])
        return package_names
        
    def get_package_data(self, package_name):
        filename = os.path.join(self.packages_dir, package_name, self.json_extension)
        with open(filename) as f:
            data = json.loads(f.read())
        return data

    def get_package_module_set(self, package_name):
        return set(self.get_package_data(package_name).modules)
        
    def get_module_set(self):
        module_set = set([])
        package_names = self.get_package_set()
        for p in package_names:
            module_set = module_set.union(self.get_package_module_set(p))
        return module_set
        
    def create_hosted_git(self):
        with open(os.path.join(self.conf_dir, "hosted_git.json")) as f:
            config = json.loads(f.read())
        return demod.hostedgit.HostedGit(config.username, config.password, config.cache_dir)
    
    
def handle_pull(module_or_package_name, pull_request):
    print('handle_pull(module_or_package_name=' + module_or_package_name + ', pull_request)')

def start_daemon():
    config = DemodConfig()
    
    package_set = config.get_package_set()
    module_set = config.get_module_set()
    
    hosted_git = config.create_hosted_git()
    hosted_git.watch_repositories(module_set.union(package_set), handle_pull)
        
        
