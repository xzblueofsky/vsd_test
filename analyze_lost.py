#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from concurrent import futures
import time
#import grpc
#import witness_pb2
#import common_pb2
import logging
import logging.handlers
import os
import datetime

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080
THRESHOLD = 0.1
TOPN = 1
#SECONDS = 50
ALARM_THRESHOLD = 0.92
 
logger = logging.getLogger("MyLogger")
os.system("mkdir -p ./log")
log_name = "./log/analyze.log"
logging.basicConfig(level=logging.DEBUG,
           format='[%(asctime)s %(name)s %(levelname)s] %(message)s',
           #format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
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
#logger.info("Timeout Threshold: %dms", conf["timeout"])
#logger.info("threadNum: %d", conf["threadNum"])


def get_capture_rate(vname):
    success_list = []
    total_list = []
    glist = result_to_list("./ground_truth/%s_label.txt" % vname)
    #tlist = result_to_list("./test_result/%s.txt" % vname)
    tlist = result_to_list("/home/dell/face/VSD/latest/result.txt.zy")
    ioucnt = 0
    for gitem in glist:
       gframeid = gitem[0]
       gid = gitem[1]
       groi = gitem[2:6]
       if gid not in total_list:
          total_list.append(gid)
       if gid in success_list:
          continue
       flag = 0
       for titem in tlist:
           if flag == 1 :
              break
           if int(gitem[0]) == int(titem[0]):
              tframeid = titem[0]
              troi = titem[2:6]
              ratio = CalRatio(groi, troi)
              if ratio > THRESHOLD:
                     ioucnt += ratio
                     logger.info("@@@@@@@@@@@@@captured@@@@@@@@@@@@@@")
                     logger.info("ratio: %s" % ratio)
                     logger.info("gframe_id: %s" % gframeid)
                     logger.info("gid: %s" % gid)
                     logger.info("groi: %s" % groi)
                     logger.info("tframe_id: %s" % tframeid )
                   #  logger.info("tid: %s" % tid)
                     logger.info("troi: %s" % troi)
                     success_list.append(gid)
                     flag = 1
    #print sorted(success_list)
    logger.info("success list: %s" % success_list )
    logger.info("total list: %s" % total_list )
    try:
       iou_avg = ioucnt*1.00/len(success_list)
    except:
       iou_avg = 0
    logger.info("iou rate: %f" % iou_avg )
    capture_rate = len(success_list)*1.0/len(total_list)
    #print "capture_rate: " + str(capture_rate)
    logger.info("capture rate: %.1f%%" % capture_rate )
    return capture_rate, iou_avg


def get_recognition_rate(mode, vname, time = 50): #mode:0=2s  mode:1=last
    glist = result_to_list("./ground_truth/%s_label.txt" % vname)
    total_rate = 0
    total_map_rate = 0
    
    if mode == 0:
       logger.info("######## video name: %s ###########" % vname)
       logger.info("mode: 2s")
       gid_list = [] #循环ground truth结果
       for i in range(0, len(glist)-1):
           gid = glist[i][1] #循环行的人id
           if gid not in gid_list: #如果这个人的id在列表中，循环下一轮，如果是第一次出现，继续往下
              gid_list.append(gid) #把这个人的id加到列表中   
              gframeid = int(glist[i][0]) 
              for item in glist:
                  if int(item[0]) == gframeid and item[1] == gid:
                     logger.info("******gid: %s*******" % gid)
                     logger.info("2s' frameid: %s" % str(gframeid+time))
                     #print gframeid, gid, groi
                     #print "**************************"
                     #print "2s' gframeid: " + str(gframeid)
                     #print "gid: " +str(gid)
                     #print "groi: " + str( groi)
                     rate = calculate_presition(gframeid+time, gid, vname) #设置取延后多少秒的结果 
                     #map_rate = 0
                     #rate, map_rate = calculate_presition(gframeid+time, gid, vname) #设置取延后多少秒的结果 
                     total_rate += rate
                     #total_map_rate += map_rate
                     logger.info("total rate: %s" % total_rate)
                     #logger.info("total map_rate: %s" % total_rate)
                     #print rate
       if len(gid_list) == 0 :
          total_recognition = 0
          #total_map_recognition = 0
       else:
          total_recognition = total_rate*1.00/len(gid_list)
          #total_map_recognition = total_map_rate*1.00/len(gid_list)
       logger.info("total recognition: %s" % total_recognition)
       #print "="*50
       #print "total_rate: " + str(total_rate)
       #print "total_num: " + str(len(gid_list))
       #print "total_recognition: " + str(total_recognition)
       #print "total_map_recognition: " + str(total_map_recognition)
       return total_recognition              
    else:
       logger.info("######## video name: %s ###########" % vname)
       logger.info("mode: last")
       gid_dict = {}
       for i in range(0, len(glist)):
           gid = glist[i][1] #循环行的人id
           gid_dict.update({gid : [int(glist[i][0]), glist[i][2:]]}) #最后列表中key value为每一个id最后的frameid和roi
 
       #print gid_dict
       for key,value in gid_dict.iteritems():
           gid = key
           gframeid = value[0]
           groi = value[1]
           #print "**************************"
           #print "last gframeid: " + str(gframeid)
           #print "gid: " +str(gid)
           #print "groi: " + str( groi)
           logger.info("******gid: %s*******" % gid)
           logger.info("last frameid: %s" % str(gframeid))
           #rate, map_rate =  calculate_presition(gframeid, gid, vname)
           map_rate =  calculate_presition(gframeid, gid, vname)
           total_rate += map_rate
           #total_map_rate += map_rate
           #print "rate: " + str(rate)
       if len(gid_dict) == 0 :
              total_recognition = 0
       else:
              total_recognition = total_rate*1.00/len(gid_dict)
       #print "="*50
       #print "total_rate: " + str(total_rate)
       #print "total_num: " + str(len(gid_dict))
       #print "total_recognition: " + str(total_recognition)
       return total_recognition
     


def calculate_presition(t_frameid, gid, vname): #输入为真实frameid，人id 
    #flist = result_to_list("./test_result/%s.txt" % vname)#读取vsd结果为list文件
    flist = result_to_list("/home/dell/face/VSD/latest/result.txt.zy")
    glist = result_to_list("./ground_truth/%s_label.txt" % vname) #读取ground truth结果为list文件
    gname = name_in_blacklist(gid)
    #print gname
    logger.info("name for search: %s " % gname)
    b_num = num_in_blacklist(gname) #此人在黑名单库的照片个数
    tmplist = []
    for fitem in flist: #循环vsd的结果list文件
       if int(fitem[0]) <= t_frameid:  
          tmplist.append(int(fitem[0])) #存起来帧数
    tmplist = sorted(tmplist)
    if len(tmplist) == 0:
       rate = 0
       return rate
    #print tmplist 


    logger.info("match tframeid in test_results: %s" % tmplist) 
    for num in reversed(tmplist): #倒序往前推, num是存起来的vsd frameid
      for fitem in flist:
         if str(fitem[0]) == str(num): #当vsd的结果中帧数等于代查找的帧数时，
          froi = fitem[2:6]
          logger.info("tframeid: %s " % fitem[0])
          logger.info("troi: %s " % fitem[2:6])
          #print "froi"
          #print froi
          for gitem in glist:
           if int(gitem[0]) == int(num) and str(gitem[1]) == str(gid): #找回groudtruth文件中这一帧且id是这个人的信息，拿到cutboard 
             logger.info("gframeid: %d " % int(gitem[0]))
             groi = gitem[2:6]
             logger.info("groi: %s " % gitem[2:6])
             #print "groi, gid, num"
             #print groi, gid, num
             iou = CalRatio(groi, froi)
             logger.info("iou: %s " % iou)
             #print "&&&&&&&&"
             #print "fid: " + str(fitem[0])
             #print "froi: " + str(froi)
             #print "iou: " +str(iou)
             if iou >= THRESHOLD:
                 logger.info("iou > %s " % THRESHOLD)
                 #print "IOU:  " + str(iou)
                 #print "~~~~~~~~~~~~"
                 topnamelist = []
                 for j in range(1,TOPN+1): #把TOPN中命中的id存为list
                   try:
                    topnamelist.append(fitem[j*3+4])
                   except:
                    topnamelist.append(0)
                 logger.info("top name list: %s" % str(topnamelist).decode('string_escape'))
                 #print "frameid: " + str(fitem[0])
                 #print "froi: " + str(froi)
                 #print "topidlist: " + str(topidlist)
                 #print "iou: " + str(iou)
                 id_cnt = 0
                 for i in topnamelist:
                    if i == gname: #当toplist中有真实id的时候 计数器+1
                        id_cnt += 1
                 acture_num = num_in_blacklist(gname) #此人在黑名单中的总数
                 if acture_num == 0:
                    rate = 0
                 else:
                    rate = id_cnt*1.00/min(TOPN, acture_num)
                 logger.info("rate: %s" % rate)
                 
                 m_cnt = 0
                 k_cnt = 0
                 map_cnt = 0
                 for j in range(0,TOPN):
                    m_cnt += 1
                    if topnamelist[j] == gname:
                       k_cnt += 1
                       #print k_cnt
                       #print m_cnt
                       map_cnt += k_cnt*1.0/m_cnt
                 
		 #print map_cnt,TOPN,acture_num
		 if acture_num == 0:
		    map_rate = 0
		 else:
                    map_rate = map_cnt*1.0/min(TOPN, acture_num)
                 #print "rate: "+str(rate)
                 #print "map_rate: " + str(map_rate)
                 logger.info("map_rate: %s" % map_rate)
                 
                 #return (rate, map_rate) 
                 return map_rate 
       #else:
    return 0
 

         

def calculate_error_alarm(vname):
    done_list = []
    total_list = []
    glist = result_to_list("./ground_truth/%s_label.txt" % vname)
    #tlist = result_to_list("./test_result/%s.txt" % vname)
    tlist = result_to_list("/home/dell/face/VSD/latest/result.txt.zy")
    erroralarm = 0
    totalalarm = len(tlist)
    
    for gitem in glist: #统计每一个gid
       gframeid = gitem[0]
       gid = gitem[1]
       groi = gitem[2:6]
       if gid not in total_list: #新出现的id，放入totallist
          total_list.append(gid)
       #if gid in done_list: #已统计过的
       #   continue
       #flag = 0
       for titem in tlist: #循环tlist与gid对比
           #if flag == 1 :
           #   break
           if int(gitem[0]) == int(titem[0]):#帧数一样的时候
              tframeid = titem[0]
              troi = titem[2:6]
              ratio = CalRatio(groi, troi)
              #print ratio
              if ratio > THRESHOLD:
                try:
                  if float(titem[8]) > ALARM_THRESHOLD:
                     gname = name_in_blacklist(gid)
                     tname = titem[7]
                     if tname != gname:
                        #print "real name:" + gname
                        #print "test result name:" + tname
                        erroralarm += 1
                except:
                  continue
                  
    #error_alarm_rate = calculate_error_alarm(gframeid, gid, vname)
    error_rate = erroralarm*1.0/totalalarm*100
    #print "erroralarm" + str(erroralarm)
    #print "totalalarm" + str(totalalarm)
    #print  "error_rate" + str(error_rate)
    #print sorted(success_list)
    return error_rate

def calculate_error_person_alarm(vname):
    done_list = []
    total_list = []
    glist = result_to_list("./ground_truth/%s_label.txt" % vname)
    #tlist = result_to_list("./test_result/%s.txt" % vname)
    tlist = result_to_list("/home/dell/face/VSD/latest/result.txt.zy")
    erroralarm = 0
    totalalarm = len(tlist)
    person_alarm = 0
    person_dict = {}
    person_rate = 0

    for gitem in glist: #统计每一个gid
       gframeid = gitem[0]
       gid = gitem[1]
       groi = gitem[2:6]
       if gid not in person_dict:
          person_dict[gid] = [0,0]
       for titem in tlist: #循环tlist与gid对比
           #if flag == 1 :
           #   break
           if int(gitem[0]) == int(titem[0]):#帧数一样的时候
              tframeid = titem[0]
              troi = titem[2:6]
              ratio = CalRatio(groi, troi)
              #print ratio
              if ratio > THRESHOLD:
                #print person_total
                try:
                  if float(titem[8]) > ALARM_THRESHOLD:
                     #person_total += 1
                     person_dict[gid][0] +=1 
                     gname = name_in_blacklist(gid)
                     tname = titem[7]
                     #print tname, gname
                     if tname != gname:
                        #print tname
                        #print gname
                        person_dict[gid][1] +=1 
                        #person_error += 1
                        #print person_error
                        #print person_total
                except:
                  continue 
         #if person_dict[gid][0] == 0:
         #   continue
         #else:
            #print "person_total:"
            #print person_error, person_total, person_alarm
            #person_alarm += person_error*1.0/person_total  
            #person_alarm += person_error*1.0/person_total  
            #print "person_error = {}, person_total = {}".format(person_error, person_total)
            #print person_error, person_total
    #print person_alarm
    
    #error_person_rate = (person_alarm*1.0/len(total_list))*100
    print person_dict
    alarm_rate_total = 0
    alarm_rate_times = 0
    lost_num = 0
    for key,value in person_dict.items():
       if value[0] == 0:
          person_rate += 0
       else:
          person_rate += value[1]*1.0/value[0]
       alarm_rate_total += value[0]
       alarm_rate_times += value[1]
       if value[0] == value[1]:
          lost_num += 1
    
    error_person_rate = person_rate*1.0/len(person_dict)*100
    error_rate =  alarm_rate_times*1.0/alarm_rate_total*100
    lost_rate = lost_num*1.0/len(person_dict)*100
    print "error_rate_new:"
    print error_rate
    print "lost_rate:"
    print lost_rate
    #print "erroralarm" + str(erroralarm)
    #print "totalalarm" + str(totalalarm)
    #print  "error_rate" + str(error_rate)
    #print sorted(success_list)
    return error_person_rate, error_rate, lost_rate


def calculate_lost_alarm(vname):
    done_list = []
    total_list = []
    glist = result_to_list("./ground_truth/%s_label.txt" % vname)
    #tlist = result_to_list("./test_result/%s.txt" % vname)
    tlist = result_to_list("/home/dell/face/VSD/latest/result.txt.zy")
    correct = 0
    totalalarm = len(tlist)

    for gitem in glist: #统计每一个gid
       gframeid = gitem[0]
       gid = gitem[1]
       groi = gitem[2:6]
       if gid not in total_list: #新出现的id，放入totallist
          total_list.append(gid)
       if gid not in done_list: #已统计过的
         #print "in in in "
         #continue
         #print gitem
         #print "~~~~"
         flag = 0
         for titem in tlist: #循环tlist与gid对比
           if flag == 1 :
              break
           if int(gitem[0]) == int(titem[0]):#帧数一样的时候
              tframeid = titem[0]
              troi = titem[2:6]
              ratio = CalRatio(groi, troi)
              #print ratio
              if ratio > THRESHOLD:
                try:
                 if float(titem[8]) > ALARM_THRESHOLD:
                     gname = name_in_blacklist(gid)
                     tname = titem[7]
                     if tname == gname:
                        correct += 1
                        #print tname
                        flag = 1
                        done_list.append(gid)
                except:
                 continue
    #print total_list
    #print done_list
    totalnum = len(total_list)
    #print total_list
    #print correct
    #print totalnum
    rate = (1 - correct*1.0/totalnum)*100
    #print rate
    return rate


def name_in_blacklist(gid):
    name = ""
    with open("Result.txt", "r") as b:
       for line in b.readlines():
          if line.split(" ")[0] == gid:
             name = line.split(" ")[1]            
    return name
    


def result_to_list(filename):
    flist = []
    with open(filename, "r") as f: # key may be duplicate
        #tlinelist = f.readlines():
        for line in f.readlines():
           #fdict[line.split(",")[0]]=line.split(",")[1:]
           flist.append(line.split(","))

    return flist

                     
def num_in_blacklist(gname):
    with open("Result.txt", "r") as b:
       cnt = 0
       for line in b.readlines():
          if line.split(" ")[1] == gname:
             cnt += 1
    #print cnt
    return cnt
              



def CalRatio(pos1, pos2):
    ratio = 0.0
    x1 = float(pos1[0])
    x2 = float(pos2[0])
    y1 = float(pos1[1])
    y2 = float(pos2[1])
    width1 = float(pos1[2])
    width2 = float(pos2[2])
    height1 = float(pos1[3])
    height2 = float(pos2[3])

    startx = min(x1, x2)
    endx = max(x1+width1, x2+width2)
    width = width1 + width2 - (endx - startx)

    starty = min(y1, y2)
    endy = max(y1+height1, y2+height2)
    height = height1 + height2 - (endy - starty)

    if (width <= 0) or (height <= 0):
        ratio = 0.0
    else:
        area = width * height
        area1 = width1 * height1
        area2 = width2 * height2
        ratio = area*1.0 / (area1 + area2 - area)
    return ratio




if __name__ == '__main__':
  #video_list = ["day_1_1","day_1_2","day_1_3","day_1_4","night_1_1","night_1_2","night_1_3","night_1_4"]
  #video_list = ["day_1_1","day_1_2","day_1_3","day_1_4","day_2_1","day_2_2","day_2_3","day_2_4","day_3_1","day_3_2","day_3_3","day_3_4","day_4_1","day_4_2","day_4_3","day_4_4","night_1_1","night_1_2","night_1_3","night_1_4","night_2_1","night_2_2","night_2_3","night_2_4","night_3_1","night_3_2","night_3_3","night_3_4","night_4_1","night_4_2","night_4_3","night_4_4"]
  #video_list = ["day_1_1", "day_1_2","day_1_3","day_1_4"]
  #video_list = ["day_1_1", "day_1_1","day_1_1","day_1_1","day_1_1", "day_1_1","day_1_1","day_1_1"]
  #video_list = ["night_4_4"]
  video_list = ["day_out"]
  #ALARM_THRESHOLD = 0.5
  avg_error_list = []
  avg_error_person_list = []
  avg_lost_list = []
  #for i in (0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9):
  with open ("totalresult.txt.zy", "w") as t:
   #for i in (0.5,0.55,0.6,0.65,0.7,0.75,0.8,0.85,0.9):
   for i in [0.6]:
    #ALARM_THRESHOLD = i
    avg_error = 0
    avg_error_person = 0
    avg_lost = 0
    t.writelines("=============%f============\n" % i)
    for vname in video_list:
     crate, iourate = get_capture_rate(vname)
     crate = float(crate)*100
     
     #rrate = float(get_recognition_rate(0, vname, 50))*100 #mode=0 : 2s, mode = 1:last
     #rrate2 = float(get_recognition_rate(0, vname, 125))*100 #mode=0 : 5s, mode = 1:last
     lrate = float(get_recognition_rate(1, vname))*100
     #error_rate = calculate_error_alarm(vname)
     error_person_rate, error_rate, lost_rate = calculate_error_person_alarm(vname)
     #lost_rate = calculate_lost_alarm(vname)
     print "="*100
     print "video %s.mp4's capture rate: %.1f%% " % (vname, crate)
     print "video %s.mp4's iou avg: %f " % (vname, iourate)
     #print "video %s.mp4's 2 second recognition rate: %.1f%%" % (vname, rrate)
     #print "video %s.mp4's 5 second recognition rate: %.1f%%" % (vname, rrate2)
     print "video %s.mp4's recognition rate: %.1f%%" % (vname, lrate)
     print "video %s.mp4's error rate: %.1f%%" % (vname, error_rate)
     print "video %s.mp4's error person rate: %.1f%%" % (vname, error_person_rate)
     print "video %s.mp4's lost rate: %.1f%%" % (vname, lost_rate)
     
     t.writelines("%.1f%%,%.1f%%,%.1f%%\n" % (error_rate, error_person_rate,lost_rate))
     #t.writelines("%.1f%%,%f,%.1f%%\n" % (crate,iourate,lrate))
     logger.info("=" * 100)
     logger.info("video %s.mp4's capture rate: %.1f%% " % (vname, crate))
     logger.info("video %s.mp4's iou rate: %f " % (vname, iourate))
     #logger.info("video %s.mp4's 2 second recognition rate: %.1f%%" % (vname, rrate))
     #logger.info("video %s.mp4's 5 second recognition rate: %.1f%%" % (vname, rrate2))
     logger.info("video %s.mp4's recognition rate: %.1f%%" % (vname, lrate))
     logger.info("video %s.mp4's error rate: %.1f%%" % (vname, error_rate))
     logger.info("video %s.mp4's lost rate: %.1f%%" % (vname, lost_rate))
     logger.info("=" * 100)
     avg_error += error_rate
     avg_error_person += error_person_rate
     avg_lost += lost_rate
    avg_error_rate = avg_error*1.0/len(video_list) 
    avg_error_person_rate = avg_error_person*1.0/len(video_list) 
    avg_lost_rate = avg_lost*1.0/len(video_list) 
    avg_error_list.append(avg_error_rate)
    avg_error_person_list.append(avg_error_person_rate)
    avg_lost_list.append(avg_lost_rate)
    t.writelines("total:%.1f%%,%.1f%%,%.1f%%\n" % (avg_error_rate, avg_error_person_rate,avg_lost_rate))
  print avg_error_list,avg_error_person_list,avg_lost_list
  #a = [708.643,378.429,135.643,158.786] 
  #b = [672.0,302.4,172.8,270.0]
  #ratio =   CalRatio(a,b)
  #print ratio
