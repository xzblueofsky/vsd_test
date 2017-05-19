#!/usr/bin/env python

import os
import sys
import cv2
import urllib
import cStringIO
import numpy as np
import re

def GetImageFromURL(URL):
    resp = urllib.urlopen(top1_URL)
    top1_image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(top1_image, cv2.IMREAD_COLOR)
    return image

def GetImageFromFrameId(frame_img_dir, frame_id):
    fn = frame_id + '.jpg'
    path = os.path.join(frame_img_dir, fn)
    image = cv2.imread(path)
    return image 

def DrawROI(frame_image, roi, color):
    roi = re.sub('\(',' ',roi)
    roi = re.sub('\)',' ',roi)
    roi = re.sub('\,',' ',roi)

    roi = roi.split()

    #print roi
    x = int(float(roi[0]))
    y = int(float(roi[1])) 
    w = int(float(roi[2])) 
    h = int(float(roi[3])) 

    cv2.rectangle(frame_image, (x,y), (x+w, y+h), color, 2)
    return frame_image

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
            ground_truth_name = elems[2]
            iou = elems[3]
            pred_roi = elems[4]
            ground_truth_roi = elems[5]
            similarity_score = elems[6]
            top1_URL = elems[7]

            top1_image = GetImageFromURL(top1_URL)
            #cv2.imshow('test',top1_image)
            frame_image = GetImageFromFrameId(frame_img_dir, frame_id) 
            #cv2.imshow(frame_id, frame_image)

            draw_image = frame_image.copy()
            DrawROI(draw_image, pred_roi, (255, 0,0))
            DrawROI(draw_image, ground_truth_roi, (0, 255,0))
            cv2.imshow(frame_id, draw_image)
            path = str(frame_id) + '.jpg'
            cv2.imwrite(path, draw_image)
            cv2.waitKey(0)
