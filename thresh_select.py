#!/usr/bin/env python

import sys
import os
import cv2
import analyze_lost
import matplotlib.pyplot as plt
import numpy as np
import datetime

if __name__=='__main__':
    if len(sys.argv) != 6:
        print( '''
        Usage: ./select_thresh.py <predict_result_path> <ground_truth_path> <id_name_map_path> <black_list_repo_dir> <IOU threshhold>
        Draw Recall-FAN(False alarm number) curve to help to select proper similarity threshold.
        ''')
        exit(1)

    predict_result_path = sys.argv[1]
    groundtruth_path = sys.argv[2]
    id_name_map_path = sys.argv[3]
    id_url_map_repo = sys.argv[4]
    iou_thresh = float(sys.argv[5])

    predict_records = analyze_lost.FileToList(predict_result_path)
    ground_truth_records = analyze_lost.FileToList(groundtruth_path)
    id_name_map = analyze_lost.GetIdNameMap(id_name_map_path)
            
    predict_records_dict = analyze_lost.GetPredictRecordDict(predict_records)
    ground_truth_records_dict = analyze_lost.GetGroundTruthRecordDict(ground_truth_records, id_name_map)

    black_list_names = analyze_lost.GetBlackListNames(id_name_map_path)
    id_url_map = analyze_lost.GetId_URL_Map(id_url_map_repo)
    alarm_similarity_thresh = 0.8

    #alarm_similarity_thresh = np.linspace(0,1,101)
    alarm_similarity_thresh = np.linspace(0.8,1,21)

    recall_list = []
    FAN_list = []
    thresh_list = []
    
    for x in alarm_similarity_thresh:
        print x
        thresh_list.append(x)
        recall = analyze_lost.GetRecall(predict_records_dict, ground_truth_records_dict, iou_thresh, x)
        recall_list.append(recall)
        print 'recall = {}'.format(recall)

        (false_alarm_rate, true_alarm_num, misidentify_num, empty_hit_num) = analyze_lost.GetFalseAlarmRate(predict_records_dict,     ground_truth_records_dict, x, iou_thresh, black_list_names, id_url_map)
        FAN_list.append( misidentify_num + empty_hit_num )
        print 'false_alarm_rate = {}'.format(false_alarm_rate)

    plt.plot(recall_list, FAN_list, 'bo')
    for (i, thresh) in enumerate(thresh_list):
        print (i, thresh)
        plt.text(recall_list[i], FAN_list[i], thresh)

    plt.xlabel('Recall')
    plt.ylabel('False Alarm Number')

    save_fn = datetime.datetime.now().strftime("%I_%M%p_%B_%d_%Y") + '.jpg'
    plt.savefig(save_fn)
    print save_fn
    plt.show()
