#!/usr/bin/env python3.3

import re

class ModuleChange:
    def __init__(self, commit_msg, deb_package, pull_request):
        self.commit_msg = commit_msg
        self.deb_package = deb_package
        self.pull_request = pull_request
        

class Proposal:
    def __init__(self, user_id, module_changes):
        self.user_id = user_id
        self.module_changes = module_changes


def build_simple_module_proposal(, pull_request)
