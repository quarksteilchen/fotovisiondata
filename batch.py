#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""chcp 65001"""
import os
import os.path

rootdir = r'Q:\fo\2009'


for subdir, dirs, files in os.walk(rootdir):
    for file in files:
        #print os.path.join(subdir, file)
        filepath = subdir + os.sep + file
        if file.endswith(".jpg") or filepath.endswith(".JPG"):
            print (filepath)
            if os.path.isfile(filepath+'.json'):
                print ('JSON file already exists. Skip API calls.')
            else:
                command = 'fotometa.py "' + filepath + '" --out "' + filepath +'.json"'
                print (command+'\n')
                os.system(command)
            print('\n')