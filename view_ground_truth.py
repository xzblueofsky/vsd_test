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

def DrawTaggedROI(frame_image, tag, roi, color):
    #print roi
    x = int(float(roi[0]))
    y = int(float(roi[1])) 
    w = int(float(roi[2])) 
    h = int(float(roi[3])) 

    cv2.rectangle(frame_image, (x,y), (x+w, y+h), color, 2)
    cv2.putText(frame_image, str(tag), (x,y), cv2.FONT_HERSHEY_SIMPLEX, 2,(255,255,255),4)
    return frame_image

if __name__=='__main__':
    print 'main'
    if len(sys.argv) != 3:
        print 'Usage: ./view_ground_truth.py <frame_image_dir> <ground_truth_path>'
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
            DrawTaggedROI(draw_image, tag[0], roi, (255, 0, 0))

        cv2.putText(draw_image, frame_id, (100,100), cv2.FONT_HERSHEY_SIMPLEX, 4,(255,255,255),4)
        #cv2.imwrite(frame_id + '.jpg', draw_image)
        cv2.imshow('ground_truth', draw_image)
        c = cv2.waitKey(0)
        if c==27:
            exit(1)
