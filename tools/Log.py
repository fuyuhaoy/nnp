#!/usr/bin/env python
'''
Created on Oct 4, 2016

@author: fu
'''

import os
import time

# log information during monitoring
class Log():
    def __init__(self, path=None):
        if path == None:
            self.filename="monitor.log"
        else:
            self.filename=path+"/monitor.log"
    # write information to log file
    def write(self, string):
        t = time.strftime("%Y-%m-%d %H:%M:%S:", time.localtime(time.time()))
        with open(self.filename, 'a') as out:
            out.write('%s %s\n' %(t, string))