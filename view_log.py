#!/usr/bin/env python

import os
import sys
import cv2
import urllib
import cStringIO
import numpy as np

if __name__=='__main__':
    print 'main'
    if len(sys.argv) != 4:
        print 'Usage:./view_log.py <frame_img_dir> <log_path> <output_dir>'
        exit(1)

    frame_img_dir = sys.argv[1]
    log_path = sys.argv[2]
    output_dir = sys.argv[3]
    
    with open(log_path) as f:
        records = f.readlines()
        for record in records:
            record.strip()
            elems = record.split('\t')
            #print elems
            frame_id = elems[0]
            pred_name = elems[1]
            recog_name = elems[2]
            iou = elems[3]
            pred_roi = elems[4]
            recog_roi = elems[5]
            similarity_score = elems[6]
            top1_URL = elems[7]
            resp = urllib.urlopen(top1_URL)
            image = np.asarray(bytearray(resp.read()), dtype="uint8")
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)
            cv2.imshow('test',image)
            cv2.waitKey(0)
