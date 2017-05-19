#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from concurrent import futures
import sys
import time
#import grpc
#import witness_pb2
#import common_pb2
import logging
import logging.handlers
import os
import datetime

logger = logging.getLogger("MyLogger")
os.system("mkdir -p ./log")
log_name = "./log/analyze.log"
logging.basicConfig(level=logging.DEBUG,
           format='[%(asctime)s %(name)s %(levelname)s] %(message)s',
           datefmt='%Y-%m-%d %H:%M:%S',
           filename=log_name,
           filemode='w')
handler = logging.handlers.RotatingFileHandler(log_name,
            maxBytes = 20971520, backupCount = 5)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
logger.info(
        "[[time.time:%s]]" % str(int(time.time())))
logger.info(
        "[[loadtest start at %s]]" % str(datetime.datetime.now()))


def FileToList(path):
    """以,为分隔符解析文件至list，用于处理predict结果文件和groundtruth文件"""
    records = []
    with open(path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            record = line.split(',')
            records.append(record)
    return records 

def GetIOU(r1, r2):
    """计算IOU"""
    x1 = float(r1[0])
    y1 = float(r1[1])
    w1 = float(r1[2])
    h1 = float(r1[3])

    x2 = float(r2[0])
    y2 = float(r2[1])
    w2 = float(r2[2])
    h2 = float(r2[3])
    
    left = max(x1, x2)
    bottom = max(y1, y2)
    top = min(y1+h1, y2+h2)
    right = min(x1+w1, x2+w2)
    
    inter_w = right-left
    inter_h = top-bottom
    if inter_w<=0 or inter_h<=0:
        inter_area=0
    else:
        inter_area = (right-left)*(top-bottom)
    iou=0
    if inter_area>0:
        iou = float(inter_area)/float(w1*h1 + w2*h2 - inter_area)
    #print 'iou={}\n'.format(iou)
    return iou
    

def GetCaptureRate(predict_records, ground_truth_records, iou_thresh):
    """ 计算抓拍率 """
    success_captured_list = []
    black_list_id_list = []
    for ground_truth_record in ground_truth_records:
        ground_truth_frame_id = int(ground_truth_record[0]) #frame_id
        gid = ground_truth_record[1] #black_list_id
        ground_truth_roi = ground_truth_record[2:6] #bounding box
        if gid not in black_list_id_list:
            black_list_id_list.append(gid)
        if gid in success_captured_list: #already captured, skip
            continue
        flag = 0
        for predict_record in predict_records:
            predict_frame_id = int(predict_record[0])
            if flag == 1 : #已经抓拍到，跳出
                break
            if predict_frame_id == ground_truth_frame_id: #在同一帧中
                predict_frame_id = predict_record[0]
                predict_roi = predict_record[2:6]
                iou = GetIOU(ground_truth_roi, predict_roi)
                if iou > iou_thresh: # IOU 超过阈值
                    logger.info("@@@@@@@@@@@@@captured@@@@@@@@@@@@@@")
                    logger.info("iou: %s" % iou)
                    logger.info("gframe_id: %s" % ground_truth_frame_id)
                    logger.info("gid: %s" % gid)
                    logger.info("groi: %s" % ground_truth_roi)
                    logger.info("tframe_id: %s" % predict_frame_id )
                    logger.info("troi: %s" % predict_roi)
                    success_captured_list.append(gid)
                    flag = 1

    logger.info("success list: %s" % success_captured_list )
    logger.info("total list: %s" % black_list_id_list )

    capture_rate = len(success_captured_list)*1.0/len(black_list_id_list)
    logger.info("capture rate: %.1f%%" % capture_rate )
    return capture_rate

def GetFinalScore(recall, false_alarm_rate):
    """
    返回得分，依据2017年5月12日 +0800 11:39, yihan@deepgl <yihan@deepgl>的邮件
    final_score = (recall*0.7 + (1-false_alarm_rate)*0.3)*100
    """
    final_score = (recall*0.7 + (1-false_alarm_rate)*0.3)*100
    return final_score

def GetFalseAlarmRate(predict_records_dict, ground_truth_records_dict, alarm_thresh, iou_thresh):
    """计算误报率 FalseAlarmRate
    FalseAlarmRate = M/N
    N: prediction 中超过alarm_thresh的总数
    M: 满足以下条件的item总数
    遍历predict_records
    0. Query与 top1 结果得分大于 alarm_thresh (条件1，2，3的前提)
    1. Query::frame_id 在GroundTruth::frame_id中不存在
    2. (Query::frame_id==GroundTruth::frame_id)
       && (Query::ROI 与 GroundTruth::ROI的iou 全部小于 iou_thresh)
    3. (Query::frame_id==GroundTruth::frame_id)
       && (Query::ROI & GroundTruth::ROI > iou_thresh)
       && Query::recog_name != GroundTruth::name)
    """
    M = 0
    N = 0
    for (pred_key, pred_value) in predict_records_dict.items():
        if pred_value[3]>alarm_thresh: #条件0
            N += 1
            pred_frame_id = pred_key[0]
            pred_roi = pred_key[1:5]
            pred_name = pred_value[2]

            pred_frame_exist_in_ground_truth = False # reset条件1的标志
            pred_iou_exist_in_ground_truth = False # reset 条件2的标志
            pred_name_is_right = False # reset 条件3的标志
            for (ground_truth_key, ground_truth_value) in ground_truth_records_dict.items():
                ground_truth_frame_id = ground_truth_key[0]

                if pred_frame_id==ground_truth_frame_id:
                    pred_frame_exist_in_ground_truth = True #条件1
                    ground_truth_roi = ground_truth_key[1:5]
                    iou = GetIOU(pred_roi, ground_truth_roi)
                    if iou>iou_thresh:
                        pred_iou_exist_in_ground_truth = True #条件2
                        pred_name = pred_value[2]
                        ground_truth_name = ground_truth_value[1]
                        if pred_name == ground_truth_name: # 条件3
                            pred_name_is_right = True 
                            #print ('pred_name = {}, ground_truth_name = {}\n'.format(pred_name, ground_truth_name))
                            break 
            if not pred_frame_exist_in_ground_truth: # 条件1
                M += 1
                continue
            if not pred_iou_exist_in_ground_truth: # 条件2
                M += 1
                continue
            if not pred_name_is_right:
                M += 1
                continue

    false_alarm_rate = float(M)/float(N)
    print ('false alarm rate calc: M = {}, N = {}, false_alarm_rate = {}\n'.format(M, N, false_alarm_rate))
    return false_alarm_rate 

def GetRecall(predict_records_dict, ground_truth_records_dict, iou_thresh):
    """计算Recall
    Recall = M/N 

    N: 所有出现在groundtruth中name不同的人的总数
    M: 满足以下条件的item总数
    1. Query::frame_id == GroundTruth::frame_id
    2. Query::ROI & GroundTruth::ROI > iou_thresh
    3. Query::recog_name == GroundTruth::name
    4. 同样name的只计入一次
    """
    unique_ground_truth_names = set()
    for (key, value) in ground_truth_records_dict.items():
        unique_ground_truth_names.add(value[1])

    N = len(unique_ground_truth_names)
    if N==0:
        print ('no name in grundtruth, check groundtruth and id_name_map')
    
    M = 0
    hit_names = set()
    for (pred_key, pred_value) in predict_records_dict.items():
        pred_frame_id = pred_key[0]
        pred_roi = pred_key[1:5]
        pred_name = pred_value[2]
        if pred_name in hit_names:
            continue
        for (ground_truth_key, ground_truth_value) in ground_truth_records_dict.items():
            ground_truth_frame_id = ground_truth_key[0]
            if pred_frame_id == ground_truth_frame_id: #条件1
                ground_truth_roi = ground_truth_key[1:5]
                iou = GetIOU(pred_roi, ground_truth_roi)
                if iou>iou_thresh: #条件2
                    ground_truth_name = ground_truth_value[1]
                    #print 'ground_truth_name = {}, pred_name={}'.format(ground_truth_name, pred_name)
                    if pred_name == ground_truth_name: #条件3
                        hit_names.add(pred_name) # 条件4

    M = len(hit_names)
    print hit_names
    recall = float(M)/float(N)
    return recall 

def GetPredictRecordDict(predict_records):
    """
    将predict_records转换为dict格式
    predict_record: <frame_id> <tracking_id> <x> <y> <width> <height> [<recog_id> <recog_name> <similarity_score>]
    predict_recors_dict:
    key: (<frame_id>, <x>, <y>, <width>, <height>)
    value: (<tracking_id>, <recog_black_list_id>, <recog_name>, <similarity_score>)
 
    """    
    predict_records_dict = {}
    for record in predict_records:
        if len(record) < 8: #抓拍，没有识别结果
            #print record
            continue 
        frame_id = int(record[0])
        tracking_id = int(record[1])
        x = float(record[2])
        y = float(record[3])
        width = float(record[4])
        height = float(record[5])
        recog_id = record[6]
        recog_name = record[7]
        similarity_score = float(record[8])

        key = (frame_id, x, y, width, height)
        value = (tracking_id, recog_id, recog_name, similarity_score)

        predict_records_dict[key] = value

    return predict_records_dict

def GetIdNameMap(id_name_map_path):
    """
    返回black_list_id到name的映射
    """
    id_name_map = {}
    with open(id_name_map_path) as f:
        lines = f.readlines()
        for line in lines:
            elems = line.split()
            black_list_id = elems[0]
            name = elems[1]
            URL = elems[2]
            id_name_map[black_list_id] = (name, URL)
    return id_name_map

def GetGroundTruthRecordDict(groundtruth_records, id_name_map):
    """
    将ground_truth_records和id_name_map_records转换为dict格式
    ground_truth_record: <frame_id> <black_list_id> <x> <y> <width> <height>
    id_map_record: <black_list_id> <name> <URL> 

    groundtruth_records_dict:
    key: (<frame_id>, <x>, <y>, <width>, <height>)
    value: (<black_list_id>, <name>, <URL>)
 
    """    

    ground_truth_records_dict = {}
    for record in ground_truth_records:
        frame_id = int(record[0])
        black_list_id = record[1]
        x = float(record[2])
        y = float(record[3])
        width = float(record[4])
        height = float(record[5])

        key = (frame_id, x, y, width, height)
        value = (black_list_id, id_name_map[black_list_id][0], id_name_map[black_list_id][1])

        ground_truth_records_dict[key] = value

    return ground_truth_records_dict

if __name__ == '__main__':
  if len(sys.argv) != 6:
    print ('Usage: ./analyze_lost.py <predict_result_path> <ground_truth_path> <id_name_map_path> <IOU threshold> <alarm similarity threshold>')
    exit(1)
  predict_result_path = sys.argv[1]
  groundtruth_path = sys.argv[2]
  id_name_map_path = sys.argv[3]
  iou_thresh = float(sys.argv[4])
  alarm_similarity_thresh = float(sys.argv[5])
  
  predict_records = FileToList(predict_result_path)
  ground_truth_records = FileToList(groundtruth_path)
  id_name_map = GetIdNameMap(id_name_map_path)
  
  predict_records_dict = GetPredictRecordDict(predict_records)
  ground_truth_records_dict = GetGroundTruthRecordDict(ground_truth_records, id_name_map)
  ## 1. 抓拍率
  capture_rate = GetCaptureRate(predict_records, ground_truth_records, iou_thresh)
  print ('capture_rate = {}\n'.format(capture_rate)) 

  ## 2. Recall
  #print predict_records_dict
  #print ground_truth_records_dict
  recall = GetRecall(predict_records_dict, ground_truth_records_dict, iou_thresh)
  print ('recall = {}\n'.format(recall))

  ## 3. 误报率
  false_alarm_rate = GetFalseAlarmRate(predict_records_dict, ground_truth_records_dict, alarm_similarity_thresh, iou_thresh)
  print ('false_alarm_rate = {}\n'.format(false_alarm_rate))

  ## 4. 得分
  final_score = GetFinalScore(recall, false_alarm_rate)
  print ('final_score = {}\n'.format(final_score))
