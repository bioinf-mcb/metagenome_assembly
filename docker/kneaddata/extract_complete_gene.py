#!/usr/bin/python

import gzip
import datetime
import sys
import re
from Bio import SeqIO

fasta=sys.argv[1]

with open(fasta, 'rU') as handle:
    for record in SeqIO.parse(handle, "fasta"):
        if re.search(r'partial=00', record.description):
            print(">"+record.description+"\n" + str(record.seq)) 
          


