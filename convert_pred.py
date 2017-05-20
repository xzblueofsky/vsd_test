#!/usr/bin/env python

import os
import sys
import analyze_lost

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'Usage: ./convert_pred.py <org_pred_file> <dest_pred_file>'
        exit(1)

    org_pred_fn = sys.argv[1]
    dest_pred_fn = sys.argv[2]

    records = analyze_lost.FileToList(org_pred_fn)
    update_reocrds = list()
    for record in records:
        x = float(record[2])
        y = float(record[3])
        w = float(record[4])
        h = float(record[5])
        center_x = x + w/2;
        center_y = y + h/2;
        x = center_x - w/2 /1.5
        y = center_y - h/2 /1.5
        w = w/1.5
        h = h/1.5
        record[2] = str(x)
        record[3] = str(y)
        record[4] = str(w)
        record[5] = str(h)
        update_reocrds.append(record)

    with open(dest_pred_fn, 'w') as f:
        for record in update_reocrds:
            item = ','.join(x for x in record)
            f.write('{}\n'.format(item))
