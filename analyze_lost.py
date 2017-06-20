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
            if '\1' in line:
                record = line.split('\1')
            else:
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

def GetLogInfoItem(pred_key, pred_value, ground_truth_key, ground_truth_value, URL):
    """
    以以下格式生成log的每一条记录：
    <frame_id> <pred_name> <ground_truth_name> <iou> <pred_roi> <ground_truth_roi> <similarity_score> <top1_url> <tracking_id>

    """
    pred_frame_id = pred_key[0]
    pred_tracking_id = pred_value[0]
    pred_name = pred_value[2]
    ground_truth_name = ground_truth_value[1]
    pred_roi = pred_key[1:5]
    ground_truth_roi = ground_truth_key[1:5]
    iou = GetIOU(pred_roi, ground_truth_roi)
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

def GetFalseAlarmRate(predict_records_dict, ground_truth_records_dict, alarm_thresh, iou_thresh, black_list_names, id_url_map):
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

    输出文件：
    1. ./log/true_alarm.log
    2. ./log/misidentify.log
    3. ./log/empty_hit.log
    """
    M = 0
    N = 0

    true_alarm_list = set()
    misidentify_list = set()
    empty_hit_list = set()
    mis_item_cnt = 0
    for (pred_key, pred_value) in predict_records_dict.items():
        pred_id = pred_value[1]
        pred_name = pred_value[2]
        similarity_score = pred_value[3]
        if pred_id not in id_url_map.keys():
            print 'not exist in black_list, pred_id = {}'.format(pred_id)
            continue

        #top1_URL = id_url_map[pred_id]
        ## 适应子勇的文件格式
        top1_URL = pred_id
        if similarity_score>alarm_thresh: #条件0
            N += 1
            pred_frame_id = pred_key[0]
            pred_roi = pred_key[1:5]

            pred_frame_exist_in_ground_truth = False # reset条件1的标志
            pred_iou_exist_in_ground_truth = False # reset 条件2的标志
            pred_name_is_right = False # reset 条件3的标志
            for (ground_truth_key, ground_truth_value) in ground_truth_records_dict.items():
                ground_truth_frame_id = ground_truth_key[0]

                if pred_frame_id==ground_truth_frame_id:
                    pred_frame_exist_in_ground_truth = True #条件1
                    ground_truth_roi = ground_truth_key[1:5]
                    iou = GetIOU(pred_roi, ground_truth_roi)
                    if iou>=iou_thresh:
                        pred_iou_exist_in_ground_truth = True #条件2
                        ground_truth_name = ground_truth_value[1]
                        #if pred_name == ground_truth_name: # 条件3
                        if pred_name == ground_truth_name or pred_name.endswith(ground_truth_name): # 条件3, predict name = 022覃晓飞, ground_truth_name = 覃晓飞 的情况
                            pred_name_is_right = True 
                        else:
                            pass
                        break 
            if not pred_frame_exist_in_ground_truth: # 条件1
                M += 1
                empty_hit_item = GetLogInfoItem(pred_key, pred_value, ground_truth_key, ground_truth_value, top1_URL) 
                empty_hit_list.add(empty_hit_item)
                continue
            if not pred_iou_exist_in_ground_truth: # 条件2
                M += 1
                empty_hit_item = GetLogInfoItem(pred_key, pred_value, ground_truth_key, ground_truth_value, top1_URL) 
                empty_hit_list.add(empty_hit_item)
                continue
            if not pred_name_is_right: # 条件3
                M += 1
                misidentify_item = GetLogInfoItem(pred_key, pred_value, ground_truth_key, ground_truth_value, top1_URL) 
                misidentify_list.add(misidentify_item)
                continue
            if pred_frame_exist_in_ground_truth and pred_iou_exist_in_ground_truth and pred_name_is_right:
                true_alarm_item = GetLogInfoItem(pred_key, pred_value, ground_truth_key, ground_truth_value, top1_URL) 
                true_alarm_list.add(true_alarm_item)
                continue

    true_alarm_log = open('./log/true_alarm.log', 'w')
    for true_alarm_item in true_alarm_list:
        true_alarm_log.write('{}\n'.format(true_alarm_item))
    true_alarm_log.close()

    misidentify_log = open('./log/misidentify.log', 'w')
    for misidentify_item in misidentify_list:
        misidentify_log.write('{}\n'.format(misidentify_item))
    misidentify_log.close()

    empty_hit_log = open('./log/empty_hit.log', 'w')
    for empty_hit_item in empty_hit_list:
        empty_hit_log.write('{}\n'.format(empty_hit_item))
    empty_hit_log.close()

    eposelon = 1e-10
    false_alarm_rate = float(M)/(float(N) + eposelon)
    print ('true_alarm_num = {}, misidentify_num = {}, empty_hit_num = {}'.format(len(true_alarm_list), len(misidentify_list), len(empty_hit_list))) 
    return (false_alarm_rate, len(true_alarm_list), len(misidentify_list), len(empty_hit_list)) 

def InsertionSort(A):
    """插入排序"""
    for j in range(1,len(A)):
        key = A[j]
        i = j-1
        #向前查找插入位置
        while i>=0 and A[i]>key:
            A[i+1] = A[i]
            i = i-1
        A[i+1] = key

def GetTrackletList(groundtruth_records):
    tracklets = []

    #group by name
    name_cluster = {} 
    for key, value in groundtruth_records.items():
        name = value[1]
        if name in name_cluster.keys():
            name_cluster[name].append((key,value))
        else:
            item = [(key,value)]
            name_cluster[name] = item
        #print name

    frame_ordered = []
    #order by frame_id
    for group_item in name_cluster.values():
        InsertionSort(group_item)
        frame_ordered.append(group_item)
        #print group_item
    #print frame_ordered

    #split by unsuccessive
    for ordered_item in frame_ordered:
        for k in range(len(ordered_item)-1):
            #print ordered_item[k][0][0]
            if len(tracklets)==0:
                first_tracklet = []
                first_tracklet.append(ordered_item[k])
                tracklets.append(first_tracklet)
                #tracklets.append(ordered_item[k])
                #print '@@@'*5
                continue
            if ordered_item[k+1][0][0] == ordered_item[k][0][0]+1:
                #print '*'*5
                tracklets[-1].append(ordered_item[k])
            else:
                #print '#'*5
                new_tracklet = []
                new_tracklet.append(ordered_item[k])
                tracklets.append(new_tracklet)
    return tracklets

def GetRecall(predict_records_dict, ground_truth_records_dict, iou_thresh, similarity_thresh):
    """计算Recall
    Recall = M/N 

    N: 所有出现在groundtruth中name不同的tracklet的总数
    M: 被击中的tracklet总数,同一个tracklet的只计入一次
    被击中条件是，tracklet内部任意一帧满足
    1. Query::frame_id == GroundTruth::frame_id
    2. Query::ROI & GroundTruth::ROI > iou_thresh
    3. Query::recog_name == GroundTruth::name
    4. Similarity>Thresh
    """
    unique_ground_truth_names = set()
    for (key, value) in ground_truth_records_dict.items():
        unique_ground_truth_names.add(value[1])

    tracklets = GetTrackletList(ground_truth_records_dict)
    #print tracklets

    N = len(tracklets)
    if N==0:
        print ('no name in grundtruth, check groundtruth and id_name_map')
    
    M = 0
    hit_tracklets = list()
    for (pred_key, pred_value) in predict_records_dict.items():
        pred_frame_id = pred_key[0]
        pred_roi = pred_key[1:5]
        pred_name = pred_value[2]
        for tracklet in tracklets:
            if tracklet in hit_tracklets:
                continue
            for (ground_truth_key, ground_truth_value) in tracklet:
                ground_truth_frame_id = ground_truth_key[0]
                if pred_frame_id == ground_truth_frame_id: #条件1
                    ground_truth_roi = ground_truth_key[1:5]
                    iou = GetIOU(pred_roi, ground_truth_roi)
                    if iou>iou_thresh: #条件2
                        ground_truth_name = ground_truth_value[1]
                        #print 'ground_truth_name = {}, pred_name={}'.format(ground_truth_name, pred_name)
                        if pred_name == ground_truth_name: #条件3
                            similarity_score = pred_value[3]
                            if similarity_score> similarity_thresh:
                                hit_tracklets.append(tracklet) # 条件4
    M = len(hit_tracklets)
    #print hit_names
    print 'Recall: M = {}, N = {}'.format(M, N)
    recall = float(M)/float(N)
    return recall 

def GetRecallByName(predict_records_dict, ground_truth_records_dict, iou_thresh, similarity_thresh):
    """计算Recall
    Recall = M/N 

    N: 所有出现在groundtruth中不同name的总数
    M: 被击中name总数,同一个name的只计入一次
    被击中条件是，属于同一个name的tracklet内部任意一帧满足
    1. Query::frame_id == GroundTruth::frame_id
    2. Query::ROI & GroundTruth::ROI > iou_thresh
    3. Query::recog_name == GroundTruth::name
    4. Similarity>Thresh
    """
    unique_ground_truth_names = set()
    for (key, value) in ground_truth_records_dict.items():
        unique_ground_truth_names.add(value[1])
    print 'unique_ground_truth_names = {}'.format(len(unique_ground_truth_names))

    tracklets = GetTrackletList(ground_truth_records_dict)
    #print tracklets

    N = len(unique_ground_truth_names)
    if N==0:
        print ('no name in grundtruth, check groundtruth and id_name_map')
    
    M = 0
    hit_names = set()
    hit_tracklets = list()
    print 'len of pred dict = {}'.format(len(predict_records))
    for (pred_key, pred_value) in predict_records_dict.items():
        pred_frame_id = pred_key[0]
        pred_roi = pred_key[1:5]
        pred_name = pred_value[2]
        if pred_name in hit_names:
            continue
        for tracklet in tracklets:
            for (ground_truth_key, ground_truth_value) in tracklet:
                ground_truth_frame_id = ground_truth_key[0]
                if pred_frame_id == ground_truth_frame_id: #条件1
                    ground_truth_roi = ground_truth_key[1:5]
                    iou = GetIOU(pred_roi, ground_truth_roi)
                    if iou>iou_thresh: #条件2
                        ground_truth_name = ground_truth_value[1]
                        if pred_name == ground_truth_name: #条件3
                            similarity_score = pred_value[3]
                            if similarity_score> similarity_thresh:
                                hit_tracklets.append(tracklet) # 条件4
                                hit_names.add(pred_name)
    M = len(hit_names)
    print hit_names
    print 'RecallByName: M = {}, N = {}'.format(M, N)
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

def GetBlackListNames(id_name_map_path):
    """
    返回black_list中人的名字列表
    """
    black_list_names = set()
    with open(id_name_map_path) as f:
        lines = f.readlines()
        for line in lines:
            elems = line.split()
            name = elems[1]
            black_list_names.add(name)
    return black_list_names

def GetGroundTruthRecordDict(ground_truth_records, id_name_map):
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

def GetId_URL_Map(black_list_dir):
    id_url_map = dict()
    for (root, subdirs, fns) in os.walk(black_list_dir):
        for fn in fns:
            path = os.path.join(root, fn)
            with open(path) as f:
                lines = f.readlines()
                for line in lines:
                    elems = line.split('\1')
                    #原来由tracking 标注工具生成的版本
                    #id_url_map[elems[0]] = elems[2]
                    #子勇的版本, 缺失black_list_id, URL充当了原来black_list_id的做用
                    id_url_map[elems[1]] = elems[0]
    return id_url_map

if __name__ == '__main__':
  if len(sys.argv) != 7:
    print ('Usage: ./analyze_lost.py <predict_result_path> <ground_truth_path> <id_name_map_path> <black_list_repo_dir> <IOU threshold> <alarm similarity threshold>')
    exit(1)
  predict_result_path = sys.argv[1]
  groundtruth_path = sys.argv[2]
  id_name_map_path = sys.argv[3]
  id_url_map_repo = sys.argv[4]
  iou_thresh = float(sys.argv[5])
  alarm_similarity_thresh = float(sys.argv[6])
  
  predict_records = FileToList(predict_result_path)
  ground_truth_records = FileToList(groundtruth_path)
  id_name_map = GetIdNameMap(id_name_map_path)
  
  predict_records_dict = GetPredictRecordDict(predict_records)
  ground_truth_records_dict = GetGroundTruthRecordDict(ground_truth_records, id_name_map)
  ## 1. 抓拍率
  capture_rate = GetCaptureRate(predict_records, ground_truth_records, iou_thresh)
  print ('capture_rate = {}'.format(capture_rate)) 

  ## 2. Recall
  #print predict_records_dict
  #print ground_truth_records_dict
  recall = GetRecallByName(predict_records_dict, ground_truth_records_dict, iou_thresh, alarm_similarity_thresh)
  print ('recall = {}'.format(recall))

  ## 3. 误报率
  black_list_names = GetBlackListNames(id_name_map_path)
  id_url_map = GetId_URL_Map(id_url_map_repo)
  (false_alarm_rate, true_alarm_num, misidentify_num, empty_hit_num) = GetFalseAlarmRate(predict_records_dict, ground_truth_records_dict, alarm_similarity_thresh, iou_thresh, black_list_names, id_url_map)
  print ('false_alarm_rate = {}'.format(false_alarm_rate))

  ## 4. 得分
  final_score = GetFinalScore(recall, false_alarm_rate)
  print ('final_score = {}'.format(final_score))
