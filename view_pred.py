#!/usr/bin/env python

import sys
import os
import cv2
import view_log
import analyze_lost
import collections

def GetFrameRoiMap(pred_records):
    frame_result_dict = dict()
    uniq_frame_ids = set()
    for record in pred_records:
        frame_id = record[0]
        if frame_id not in uniq_frame_ids:
            uniq_frame_ids.add(frame_id)
            frame_result_dict[frame_id] = list()
            frame_result_dict[frame_id].append(record[2:6]) 
        else:
            frame_result_dict[frame_id].append(record[2:6])
    #print frame_result_dict
    return frame_result_dict

if __name__=='__main__':
    print 'main'
    if len(sys.argv) != 3:
        print 'Usage: ./view_pred.py <frame_image_dir> <pred_path>'
        exit(1)
    frame_dir = sys.argv[1]
    pred_path = sys.argv[2]

    pred_records = analyze_lost.FileToList(pred_path)

    frame_result_dict = GetFrameRoiMap(pred_records)
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
            roi = ','.join(x for x in tag)
            view_log.DrawROI(draw_image, roi, (255, 0, 0))

        cv2.putText(draw_image, frame_id, (100,100), cv2.FONT_HERSHEY_SIMPLEX, 4,(255,255,255),4)
        cv2.imshow('pred_image', draw_image)
        cv2.waitKey(0)
