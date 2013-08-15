#!/usr/bin/env python3.3

import git

def propose(proposal):
    
    # Put it to the vote.
    
    # Once approved:
    git.make_change(proposal)
    
