#!/usr/bin/env python

import sys
import csv

def main():
    if len(sys.argv) != 2:
        print 'Usage: {0} [input]'.format(sys.argv[0])
        return
    input_path = sys.argv[1]

    with open(input_path, 'r') as input_file:
        for timestamp, clock, data in csv.reader(input_file):
            timestamp = float(timestamp)
            clock, data = int(clock), int(data)
            print repr(timestamp), repr(clock), repr(data)

if __name__ == '__main__':
    main()
