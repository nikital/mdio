#!/usr/bin/env python

import sys
import csv
from collections import namedtuple

class MdioParser(object):
    Row = namedtuple('Row', ['timestamp', 'clock', 'data'])

    def __init__(self):
        super(MdioParser, self).__init__()
        self.rows = []

    def add_row(self, row):
        self.rows.append(row)

    def get_packets(self):
        for row in self.rows:
            yield row

def main():
    if len(sys.argv) != 2:
        print 'Usage: {0} [input]'.format(sys.argv[0])
        return
    input_path = sys.argv[1]

    parser = MdioParser()

    with open(input_path, 'r') as input_file:
        for timestamp, clock, data in csv.reader(input_file):
            timestamp = float(timestamp)
            clock, data = int(clock), int(data)
            parser.add_row(MdioParser.Row(timestamp, clock, data))

    for packet in parser.get_packets():
        print packet

if __name__ == '__main__':
    main()
