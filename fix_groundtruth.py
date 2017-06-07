#!/usr/bin/env python

import os
import sys
import cv2
import collections

if __name__=='__main__':
    print 'main'
    if len(sys.argv) != 4:
        print 'Usage: ./fix_groundtruth.py <label_file_path> <cleaned_tracklets_folder> <output_file>'
        exit(1)

    label_file_path = sys.argv[1]
    cleaned_tracklets_folder = sys.argv[2]
    output_file_path = sys.argv[3]

    cleaned_records = []
    cleaned_records_dict = [] 
    ordered_dict = {}
    for (root, subdirs, fns) in os.walk(cleaned_tracklets_folder):
        for fn in fns:
            image_path = os.path.join(root, fn)
            fn = fn[:-4]
            info = fn.split('_')
            #print info
            record = ','.join(info)
            cleaned_records.append((int(info[0]), record) )
            #cleaned_records_dict[int(info[0])] = record
            print record
    
    #sorted(cleaned_records)

    #od = collections.OrderedDict(sorted(cleaned_records_dict.items()))
    cleaned_records.sort()
    with open(output_file_path, 'w') as f:
        for key, value in cleaned_records:
            f.write('{}\n'.format(value))
