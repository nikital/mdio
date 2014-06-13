#!/usr/bin/env python

import sys
import csv
import argparse
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

    def read_bits_as_int(self, bit_count):
        bits, first_timestamp = self._read_bits_array(bit_count)
        result = 0
        for bit in bits:
            result <<= 1
            result |= bit
        return result, first_timestamp

    def _read_bits_array(self, bit_count):
        bits = []
        first_timestamp = None
        while len(bits) < bit_count:
            if not self.i < len(self.rows):
                raise EOFError()

            row = self.rows[self.i]
            if self._should_read_bit(self.i):
                if first_timestamp is None:
                    first_timestamp = row.timestamp
                bits.append(row.data)
            self.i += 1

        return bits, first_timestamp

    def _should_read_bit(self, i):
        if self.rows[i].clock != self.clock_phase:
            return False

        if i == 0:
            return True
        if self.rows[i - 1].clock == self.clock_phase:
            return False
        return True

MdioPacket = namedtuple('MdioPacket', [
    'timestamp', 'operation',
    'phy_address', 'reg_address',
    'data'
    ])

def format_packet(packet):
    return '{:.7f} {} {:#04x} {:#04x} {:#06x}'.format(
            packet.timestamp,
            'w' if packet.operation == 1 else 'r',
            packet.phy_address, packet.reg_address,
            packet.data)

class MdioParser(object):
    def __init__(self, stream, is_broadcom):
        super(MdioParser, self).__init__()
        self.stream = stream
        self.is_broadcom = is_broadcom
        if not is_broadcom:
            raise NotImplementedError('Only Broadcom is supported')

    def get_packets(self):
        try:
            while True:
                self.stream.set_clock_phase(0)
                timestamp = self._read_until_start()

                operation, _ = self.stream.read_bits_as_int(2)
                phy_address, _ = self.stream.read_bits_as_int(5)
                reg_address, _ = self.stream.read_bits_as_int(5)
                turn_around, _ = self.stream.read_bits_as_int(2)
                data, _ = self.stream.read_bits_as_int(16)

                packet = MdioPacket(timestamp, operation,
                        phy_address, reg_address,
                        data)
                yield packet

        except EOFError:
            pass

    def _read_until_start(self):
        bit = 1
        preamble_count = 0
        while bit != 0:
            bit, timestamp = self.stream.read_bits_as_int(1)
            preamble_count += 1

        assert (preamble_count >= 16)
        next_bit, _ = self.stream.read_bits_as_int(1)
        assert (next_bit == 1)

        return timestamp

def read_stream_from_csv(input_path):
    stream = MdioStream()
    with open(input_path, 'r') as input_file:
        for timestamp, clock, data in csv.reader(input_file):
            timestamp = float(timestamp)
            clock, data = int(clock), int(data)
            stream.add_row(MdioStream.Row(timestamp, clock, data))
    return stream

def parse_args():
    parser = argparse.ArgumentParser(description=
            'Decode MDIO packets from raw bus')
    parser.add_argument('-b', '--broadcom', action='store_true', default=False,
            help='use Broadcom non-standard clock')
    parser.add_argument('input_path')
    return parser.parse_args()

def main():
    args = parse_args()

    stream = read_stream_from_csv(args.input_path)

    parser = MdioParser(stream, args.broadcom)
    for packet in parser.get_packets():
        print format_packet(packet)

if __name__ == '__main__':
    main()
