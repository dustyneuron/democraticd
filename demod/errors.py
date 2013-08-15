#!/usr/bin/env python3.3

import repr

class ArgsError(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return repr.repr(self.value)
    
