#!/usr/bin/env python

import os
import sys

if __name__=='__main__':
    if len(sys.argv) !=2:
        print 'Usage: ./get_pred_name_list.py <dir>'
        exit(1)

    root_dir = sys.argv[1]

    pred_names = set()
    pred_dict = dict()
    for (root, subdirs, fns) in os.walk(root_dir):
        for fn in fns:
            if fn.endswith('info.txt'):
                path = os.path.join(root, fn)

                with open(path, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if 'predict name' in line:
                            elems = line.split()
                            pred_name = elems[-1]
                            pred_names.add(pred_name)
                            subdir = os.path.basename(root)
                            print 'pred_name = {}, subdir = {}'.format(pred_name, subdir)
                            if pred_name in pred_dict.keys():
                                pred_dict[pred_name].append(subdir)
                            else:
                                value = [subdir]
                                pred_dict[pred_name] = value
    
    print pred_names
    print len(pred_names)
    for key, value in pred_dict.items():
        print('{}:{}'.format(key, value))
