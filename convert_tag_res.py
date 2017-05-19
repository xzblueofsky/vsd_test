#!/usr/bin/env python

import os
import sys
import analyze_lost

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'Usage: ./convert_tag_res.py <org_tag_fiel> <dest_tag_file>'
        exit(1)

    org_tag_fn = sys.argv[1]
    dest_tag_fn = sys.argv[2]

    tag_X_res = 1920.0
    tag_Y_res = 1080.0
    dest_X_res = 1280.0
    dest_Y_res = 720.0

    x_ratio = dest_X_res/tag_X_res;
    y_ratio = dest_Y_res/tag_Y_res;

    records = analyze_lost.FileToList(org_tag_fn)
    update_reocrds = list()
    for record in records:
        x = float(record[2])*x_ratio
        y = float(record[3])*y_ratio
        w = float(record[4])*x_ratio
        h = float(record[5])*y_ratio
        record[2] = str(x)
        record[3] = str(y)
        record[4] = str(w)
        record[5] = str(h)
        update_reocrds.append(record)

    with open(dest_tag_fn, 'w') as f:
        for record in update_reocrds:
            item = ','.join(x for x in record)
            f.write('{}\n'.format(item))

