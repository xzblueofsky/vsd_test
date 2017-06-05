#!/usr/bin/env python

import sys
import os
import cv2
import view_log
import analyze_lost
import collections

def GetFrameRoiMap(ground_truth_records):
    frame_result_dict = dict()
    uniq_frame_ids = set()
    for record in ground_truth_records:
        frame_id = int(record[0])
        if frame_id not in uniq_frame_ids:
            uniq_frame_ids.add(frame_id)
            frame_result_dict[frame_id] = list()
            frame_result_dict[frame_id].append(record[1:]) 
        else:
            frame_result_dict[frame_id].append(record[1:])
    #print frame_result_dict
    return frame_result_dict

def GetTaggedROI(frame_image, roi, ratio):
    #print roi

    x = int(float(roi[0]))
    y = int(float(roi[1])) 
    w = int(float(roi[2])) 
    h = int(float(roi[3])) 

    new_w = w*ratio
    new_h = h*ratio
    new_x = x+w/2-new_w/2
    if new_x<0:
        new_x = 0
    new_y = y+h/2-new_h/2
    if new_y<0:
        new_y = 0
    if x+new_w>frame_image.shape[1]:
        new_w = frame_image.shape[1]-new_x
    if y+new_h>frame_image.shape[0]:
        new_h = frame_image.shape[0]-new_y

    return frame_image[new_y:new_y+new_h,new_x:new_x+new_w,:]

if __name__=='__main__':
    print 'main'
    if len(sys.argv) != 3:
        print 'Usage: ./save_tag_snapshot.py <frame_image_dir> <ground_truth_path>'
        exit(1)
    frame_dir = sys.argv[1]
    ground_truth_path = sys.argv[2]

    ground_truth_records = analyze_lost.FileToList(ground_truth_path)

    frame_result_dict = GetFrameRoiMap(ground_truth_records)
    ordered_frame_result_dict = collections.OrderedDict(sorted(frame_result_dict.items()))
    #ordered_frame_result_dict = frame_result_dict

    for frame_id, tags in ordered_frame_result_dict.items():
        num = int(frame_id)
        frame_id = str(int(frame_id))
        #print frame_id
        frame_image = view_log.GetImageFromFrameId(frame_dir, frame_id)
        draw_image = frame_image.copy()
        #rois = list()
        for tag in tags:
            roi = [x for x in tag[1:]]
            print 'tag = {}, roi={}'.format(tag[0], roi)
            track_id = tag[0]
            if not os.path.exists(track_id):
                os.mkdir(track_id)

            roi_path = '{}/{}_{}_{}_{}_{}_{}.jpg'.format(track_id, frame_id, track_id, roi[0], roi[1], roi[2], roi[3])
            roi = GetTaggedROI(frame_image, roi, 1.5)
            cv2.imwrite(roi_path, roi)
            #cv2.imshow('roi', roi)
            #cv2.waitKey(0)

