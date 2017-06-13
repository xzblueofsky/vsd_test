#!/usr/bin/env python

import os
import sys
import matplotlib.pyplot as plt
import datetime

def main():
    print 'main'
    pass

def GetFileList(list_file):
    file_list = []
    with open(list_file) as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            file_list.append(line)
    return file_list

def DrawCompareFig(file_list):
    for data_file in file_list:
        base_name = os.path.basename(data_file)
        pos = base_name.find('.')
        base_name = base_name[:pos]
        print base_name
        recall_list = []
        FAN_list = []
        thresh_list = []
        with open(data_file) as f:
            lines = f.readlines()
            for line in lines:
                elems = line.split()
                recall_list.append(float(elems[0]))
                FAN_list.append(float(elems[1]))
                thresh_list.append(float(elems[2]))
        plt.plot(recall_list, FAN_list, 'o-', label=base_name)
        #plt.legend([base_name], loc='upper left')
        plt.legend(loc='upper left')
        for (i, thresh) in enumerate(thresh_list):
            plt.text(recall_list[i], FAN_list[i], thresh)
    plt.xlabel('Recall')
    plt.ylabel('FAN(False Alarm Number)')
    plt.show()

    save_fn = datetime.datetime.now().strftime("%I_%M%p_%B_%d_%Y") + '.jpg'
    plt.savefig(save_fn)
    print save_fn

if __name__=='__main__':
    if len(sys.argv) != 2:
        print 'Usage: ./comp_curve.py <curve_list_file>'
        exit(1)
    curve_list_file = sys.argv[1]

    file_list = GetFileList(curve_list_file)
    print file_list

    DrawCompareFig(file_list)
    main()
