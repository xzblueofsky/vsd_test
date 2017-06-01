#!/usr/bin/env python

import os
import sys
import cv2
import urllib
import cStringIO
import numpy as np
import re
import shutil
import errno

def GetImageFromURL(URL):
    try:
        resp = urllib.urlopen(top1_URL)
    except:
        print top1_URL
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

def GetRoiSubImage(frame_image, roi):
    roi = re.sub('\(',' ',roi)
    roi = re.sub('\)',' ',roi)
    roi = re.sub('\,',' ',roi)

    roi = roi.split()

    #print roi
    x = int(float(roi[0]))
    y = int(float(roi[1])) 
    w = int(float(roi[2])) 
    h = int(float(roi[3])) 

    sub_image = frame_image[y:y+h,x:x+w]
    return sub_image

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def GetDestDir(frame_id, pred_roi, log_path, output_dir):

    log_basename = os.path.basename(log_path)
    pos = log_basename.find('.')
    log_basename = log_basename[:pos]
    dest_dir = os.path.join(output_dir, log_basename)

    sub_dir = '_'.join(x for x in (frame_id, pred_roi))
    sub_dir = re.sub('\(', '', sub_dir)
    sub_dir = re.sub('\)', '', sub_dir)
    sub_dir = re.sub('\ ', '', sub_dir)
    sub_dir = re.sub('\,', '_', sub_dir)
    dest_dir = os.path.join(dest_dir, sub_dir)
    return dest_dir

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
            #cv2.imshow('top1',top1_image)
            frame_image = GetImageFromFrameId(frame_img_dir, frame_id) 
            #cv2.imshow(frame_id, frame_image)

            draw_image = frame_image.copy()
            DrawROI(draw_image, pred_roi, (255, 0,0))
            DrawROI(draw_image, ground_truth_roi, (0, 255,0))
            #cv2.imshow(frame_id, draw_image)

            query_image = GetRoiSubImage(frame_image, pred_roi)
            #cv2.imshow('query_image', query_image)

            ground_truth_image = GetRoiSubImage(frame_image, ground_truth_roi)
            #cv2.imshow('ground_truth_image', ground_truth_image)

            dest_dir = GetDestDir(frame_id, pred_roi, log_path, output_dir)
            print dest_dir
            
            if not os.path.exists(dest_dir):
                mkdir_p(dest_dir)

            det_image_path = os.path.join(dest_dir, frame_id) + '.jpg'
            cv2.imwrite(det_image_path, draw_image)

            query_image_path = os.path.join(dest_dir, 'query.jpg')
            cv2.imwrite(query_image_path, query_image)

            ground_truth_path = os.path.join(dest_dir, 'ground_truth.jpg')
            cv2.imwrite(ground_truth_path, ground_truth_image)

            top1_path = os.path.join(dest_dir, 'top1.jpg')
            cv2.imwrite(top1_path, top1_image)

            info_path = os.path.join(dest_dir, 'info.txt')

            with open(info_path, 'w') as f:
                f.write('iou = {}\n'.format(iou))
                f.write('similarity_score = {}\n'.format(similarity_score)) 
                f.write('predict name = {}\n'.format(pred_name))
                f.write('ground_truth_name = {}\n'.format(ground_truth_name))
                f.write('top1_URL = {}\n'.format(top1_URL))
