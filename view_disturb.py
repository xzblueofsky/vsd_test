#!/usr/bin/env python

import sys
import os
import cv2
import analyze_lost
import analyze_disturb
import matplotlib.pyplot as plt
import numpy as np
import datetime

if __name__=='__main__':
    if len(sys.argv) != 2:
        print( '''
        Usage: ./view_disturb.py <predict_result_path>
        Draw thresh-FAN(False alarm number) curve.
        ''')
        exit(1)

    predict_result_path = sys.argv[1]

    predict_records = analyze_lost.FileToList(predict_result_path)
            
    predict_records_dict = analyze_lost.GetPredictRecordDict(predict_records)

    #alarm_similarity_thresh = np.linspace(0,1,101)
    alarm_similarity_thresh = np.linspace(0.8,1,21)

    FAN_list = []
    thresh_list = []
    
    for x in alarm_similarity_thresh:
        print x
        thresh_list.append(x)

        empty_hit_num = analyze_disturb.GetAlarm(predict_records_dict,x)
        FAN_list.append( empty_hit_num )

    plt.plot(thresh_list, FAN_list, 'bo')
    for (i, thresh) in enumerate(thresh_list):
        plt.text(thresh_list[i], FAN_list[i], thresh)
        print ('thresh = {}, FAN = {}'.format(thresh, FAN_list[i]))

    plt.xlabel('Thresh')
    plt.ylabel('False Alarm Number')
    plt.xlim([thresh_list[0],1])

    save_fn = datetime.datetime.now().strftime("%I_%M%p_%B_%d_%Y") + '.jpg'
    plt.savefig(save_fn)
    print save_fn
    plt.show()
