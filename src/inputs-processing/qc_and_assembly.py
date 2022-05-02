import os 
import pandas as pd
import json 
import re

import sys

study_path = sys.argv[1]
meta = pd.read_csv(os.path.join(study_path, "SraRunTable.txt"))
counts = meta.Title.value_counts()
print("Found samples:")
print(counts.index[0], '\t', counts.values[0])

# getting sorted lists of forward and reverse reads from a folder
forward, reverse = [os.path.join(study_path, file) for file in sorted(os.listdir(study_path)) if file.endswith("_1.fastq.gz")], \
                   [os.path.join(study_path, file) for file in sorted(os.listdir(study_path)) if file.endswith("_2.fastq.gz")]

# template
qc_assemble = {"qc_and_assemble.sampleInfo": []}
# adding files to json
for r1, r2 in zip(forward, reverse):
    qc_assemble["qc_and_assemble.sampleInfo"].append({"file_r1": r1, "file_r2": r2})

# writing input json
with open('inputs.json', 'w') as f:
    json.dump(qc_assemble, f, indent=4, sort_keys=True, ensure_ascii=False)