from __future__ import print_function
from __future__ import division
import sys
import os
import glob

import matplotlib.pyplot as plt




def twos_complement(input_value, num_bits=48):
    '''Calculates a two's complement integer from the given input value's bits'''
    value = int(input_value, 16)
    mask = 2**(num_bits - 1)
    return -(value & mask) + (value & ~mask)


def single16_word_int (v):
    value_low = int(v, 16)
    if value_low >= 65536/2:
        value_low = value_low - 65536
    return value_low




def read_file (filename):
    """
    Read a file in partial hex format
    """

    fi = open(filename)

    for i in range(8):
        print(fi.readline().strip())














read_file(sys.argv[1])
