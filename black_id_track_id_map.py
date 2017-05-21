#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import analyze_lost

def GetIdMapList(id_map_path):
    map_list = []
    with open(id_map_path) as f:
        lines = f.readlines()
        for line in lines:
            elems = line.split()
            map_list.append(elems)
    return map_list

if __name__=='__main__':
    print 'main'
    if len(sys.argv)!=4:
        print '''Usage: ./black_id_track_id_map.py <track_id_tag_file_path> <black_id_track_id_map_file> <output_label>\n
        功能:将track_id_tag_file> 中所有track_id替换为对应的black_list_id，删除其余结果，另存为output_label指定位置

        ***<track_id_tag_file_path> -- 标注生成的文件，格式为：
        <frame_id> <track_id> <x> <y> <w> <h>
        000001,1,991.5,288,93,94.5
        000001,2,1230,199.5,79.5,102
        000001,3,991.5,202.5,55.5,81
        000002,1,987.9,288,92.7,95.1
        000002,2,1227,202.125,79.875,103.125
        000002,3,987.5,201.5,55.75,80.25
        000003,1,984.3,288,92.4,95.7
        000003,2,1224,204.75,80.25,104.25
        
        ***<black_id_track_id_map_file> -- 黑名单ID和track_id映射关系，格式为：
        <blacklist_id> [track_id0, track_id1, ...]
        22351429 2 15
        52367262 3
        52308398 7 14
        52409813 1 13
        52598898 6 9
        '''
    tag_file_path = sys.argv[1]
    id_map_path = sys.argv[2]
    output_path = sys.argv[3]

    map_list = GetIdMapList(id_map_path)
    print map_list

    tag_records = analyze_lost.FileToList(tag_file_path)
    #print tag_records

    black_list_records = []
    for tag_record in tag_records:
        for map_record in map_list:
            for x in map_record[1:]:
                if tag_record[1] == x:
                    label_record = tag_record
                    label_record[1] = map_record[0]
                    black_list_records.append(label_record)
                else:
                    pass

    #print black_list_records
    with open(output_path, 'w') as f:
        for label_record in black_list_records:
            info = ','.join(x for x in label_record)
            f.write('{}\n'.format(info))
