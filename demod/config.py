import demod.hostedgit

import os
import json


class Config:
    def __init__(self):
        self.conf_dir = "/home/tom/.demod/"
        self.packages_dir = os.path.join(self.conf_dir, "packages")
        self.pull_requests_dir = os.path.join(self.conf_dir, "pull-requests")
        self.json_extension = ".json"
        
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
        
    def create_hosted_git(self):
        with open(os.path.join(self.conf_dir, "hosted_git.json"), 'rt') as f:
            config = json.loads(f.read())
        return demod.hostedgit.HostedGit(config['username'], config['password'])

    def read_pull_requests(self, repo, pr_class_type):
        filename = os.path.join(self.pull_requests_dir, repo + self.json_extension)
        pr_list = []
        with open(filename, 'rt') as f:
            data = json.loads(f.read())
        for (issue_id, d) in data.items():
            pr = pr_class_type()
            for (k, v) in d.items():
                pr.__dict__[k] = v
            pr_list.append(pr)
            
        return pr_list

    def write_pull_requests(self, repo, pr_list):
        filename = os.path.join(self.pull_requests_dir, repo + self.json_extension)
        data = {}
        for pr in pr_list:
            data[pr.issue_id] = vars(pr)
            
        with open(filename, 'wt') as f:
            f.write(json.dumps(data, sort_keys=True, indent=4))
        


