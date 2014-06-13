#!/usr/bin/env python

import sys
import csv
from collections import namedtuple
from itertools import ifilter

class MdioStream(object):
    Row = namedtuple('Row', ['timestamp', 'clock', 'data'])

    def __init__(self):
        super(MdioStream, self).__init__()
        self.rows = []
        self.i = 0
        self.clock_phase = 0

    def add_row(self, row):
        self.rows.append(row)

    def set_clock_phase(self, clock_phase):
        self.clock_phase = clock_phase

    def read_bits_array(self, bit_count):
        bits = []
        first_timestamp = None
        while len(bits) < bit_count:
            if not self.i < len(self.rows):
                raise EOFError()

            row = self.rows[self.i]
            if self._is_data(self.i):
                if first_timestamp is None:
                    first_timestamp = row.timestamp
                bits.append(row.data)
            self.i += 1

        return bits, first_timestamp

    def read_bits_as_int(self, bit_count):
        bits, first_timestamp = self.read_bits_array(bit_count)
        result = 0
        for bit in bits:
            result <<= 1
            result |= bit
        return result, first_timestamp

    def _is_data(self, i):
        if self.rows[i].clock != self.clock_phase:
            return False

        if i == 0:
            return True
        if self.rows[i - 1].clock == self.clock_phase:
            return False
        return True

class MdioParser(object):
    def __init__(self, stream):
        super(MdioParser, self).__init__()
        self.stream = stream

    def get_packets(self):
        try:
            while True:
                self.stream.set_clock_phase(1)
                timestamp = self._find_start()
                yield timestamp

        except EOFError:
            pass

    def _find_start(self):
        bit = 1
        while bit != 0:
            bit, timestamp = self.stream.read_bits_as_int(1)

        next_bit, _ = self.stream.read_bits_as_int(1)
        assert (next_bit == 1)

        return timestamp

def parse_packets_from_stream(stream):
    [
        PREAMBLE,
        START,
        OPERATION,
        PHY_ADDRESS,
        REG_ADDRESS,
        TURN_AROUND,
        DATA,
    ] = range(7)

def main():
    if len(sys.argv) != 2:
        print 'Usage: {0} [input]'.format(sys.argv[0])
        return
    input_path = sys.argv[1]

    stream = MdioStream()

    with open(input_path, 'r') as input_file:
        for timestamp, clock, data in csv.reader(input_file):
            timestamp = float(timestamp)
            clock, data = int(clock), int(data)
            stream.add_row(MdioStream.Row(timestamp, clock, data))

    parser = MdioParser(stream)
    print parser.get_packets().next()

if __name__ == '__main__':
    main()
