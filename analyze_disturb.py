#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from concurrent import futures
import sys
import time
import os
import datetime
import analyze_lost

os.system("mkdir -p ./log")

def GetLogInfoItem(pred_key, pred_value):
    """
    以以下格式生成log的每一条记录：
    <frame_id> <pred_name> <ground_truth_name> <iou> <pred_roi> <ground_truth_roi> <similarity_score> <top1_url> <tracking_id>

    """
    pred_frame_id = pred_key[0]
    pred_tracking_id = pred_value[0]
    URL = pred_value[1]
    pred_name = pred_value[2]
    ground_truth_name = '$' 
    pred_roi = pred_key[1:5]
    ground_truth_roi = '($,$,$,$)'
    iou = '$'
    similarity_score = pred_value[3]
    
    item_info = list()
    item_info.append(pred_frame_id)
    item_info.append(pred_name)
    item_info.append(ground_truth_name)
    item_info.append(iou)
    item_info.append(pred_roi)
    item_info.append(ground_truth_roi)
    item_info.append(similarity_score)
    item_info.append(URL)
    item_info.append(pred_tracking_id)
    info_item_str = '\t'.join(str(x) for x in item_info)
    return info_item_str

def GetAlarm(predict_records_dict, alarm_thresh):
    """计算误报 FalseAlarm
    M: 满足以下条件的item总数
    遍历predict_records
    1. Query与 top1 结果得分大于 alarm_thresh
    输出文件：
    1. ./log/empty_hit.log

    备注：
     log以以下格式生成log的每一条记录：$
     <frame_id> <pred_name> <ground_truth_name> <pred_roi> <similarity_score> <top1_url> <tracking_id>

     对于却省的项，均以'$'填充
    """
    M = 0

    empty_hit_list = set()
    mis_item_cnt = 0
    for (pred_key, pred_value) in predict_records_dict.items():
        pred_id = pred_value[1]
        pred_name = pred_value[2]
        similarity_score = pred_value[3]

        #top1_URL = id_url_map[pred_id]
        ## 适应子勇的文件格式
        top1_URL = pred_id
        if similarity_score>alarm_thresh: #条件0
            M += 1

            pred_frame_id = pred_key[0]
            pred_roi = pred_key[1:5]

            empty_hit_item = GetLogInfoItem(pred_key, pred_value) 
            empty_hit_list.add(empty_hit_item)

    empty_hit_log = open('./log/empty_hit.log', 'w')
    for empty_hit_item in empty_hit_list:
        empty_hit_log.write('{}\n'.format(empty_hit_item))
    empty_hit_log.close()

    return M

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print ('Usage: ./analyze_disturb.py <predict_result_path> <alarm similarity threshold>')
        exit(1)
    predict_result_path = sys.argv[1]
    alarm_similarity_thresh = float(sys.argv[2])

    predict_records = analyze_lost.FileToList(predict_result_path)
    predict_records_dict = analyze_lost.GetPredictRecordDict(predict_records)
    ##报警统计 
    false_alarm_num = GetAlarm(predict_records_dict, alarm_similarity_thresh)
    print 'false_alarm_num = {}'.format(false_alarm_num)
