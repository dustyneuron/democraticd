#!/usr/bin/env python3.3

import voting
import proposal
import re

def handle_proposal(user_id, pull_requests):
    module_changes = []
    for pull_request in pull_requests:
        # In a sandbox:
        # download git repo, find out which deb package it belongs to
        # demod deb packages install a config file (/etc/demod/{package}.json):
        # eg demod-voting.json: {[demod-voting-html, demod-misc]}
        #   demod-forum.json: {[demod-misc]}
        # 
        # check against pull_request.original_url

        deb_package = "demod-mailer-tracker" # pkg will be roboji specific, as it has ptrs to roboji upstreams.
        # do some basic sanity tests on it
        # create a proposal object
        module_changes.add(proposal.ModuleChange("commit msg blah", deb_package, pull_request))
        # wipe sandbox
        
    prop = proposal.Proposal(user_id, module_changes)
    voting.propose(prop)
    
def make_change(prop):
    for module_change in prop.module_changes:
        pull_request = module_change.pull_request
        
    # push to github repo
    
    deb.build(prop.deb_package)

