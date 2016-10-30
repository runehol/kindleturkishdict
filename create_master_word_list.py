#!/usr/bin/env pypy3

from collections import defaultdict
import argparse
import os.path
import time
import locale


locale.setlocale(locale.LC_ALL, 'tr_TR') #make sure string lowercase are turkish aware

freqlist = defaultdict(float)

def process_frequency_list_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            v = line.strip().split()
            if len(v) == 2:
                word = v[0].replace("“", "")
                word = word.lower()

                yield word, int(v[1])


def read_freq_list(freq_list_name, scale):
    for word, count in process_frequency_list_file(freq_list_name):
        freqlist[word] += count*scale

def filter_freq_lists(min_frequency):

    for word, v in list(freqlist.items()):
        if v < min_frequency:
            del freqlist[word]
            
        

        
def gen_freq_list(dest_file, freq_list_names, min_frequency):

    filter_by_freq_list = freq_list_names != []
    for fname in freq_list_names:
        print("Reading frequency list %s..." % (fname,))
        read_freq_list(fname, 1.0)

    pre_freq_list_len = len(freqlist)
    filter_freq_lists(min_frequency)
    print("Filtered frequency list of %d entries down to %d entries\n" % (pre_freq_list_len, len(freqlist)))

    dest = open(dest_file, "w")
    for word in freqlist.keys():
        dest.write("%s\n" % (word,))

    dest.close()
                
        
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a master frequency list suitable to pass to a morphological analyzer')
    parser.add_argument('--dest-file',
                    help='Destination file')
    parser.add_argument('--frequency-list', nargs='*', default=[],
                    help='Frequency list to filter by (more than one allowed)')
    parser.add_argument('--min-word-frequency', type=float, default=0.0,
                    help='Minimum word frequency to be considered (measured in number of occurrences)')

    arg = parser.parse_args()
    gen_freq_list(arg.dest_file, arg.frequency_list, arg.min_word_frequency)
