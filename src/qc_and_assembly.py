import os 
import json 
import re

import sys

study_path = sys.argv[1]
study_path = os.path.abspath(study_path)

threads = sys.argv[2]

# getting sorted lists of forward and reverse reads from a folder
forward, reverse = [os.path.join(study_path, file) for file in sorted(os.listdir(study_path)) if file.endswith("_1.fastq.gz")], \
                   [os.path.join(study_path, file) for file in sorted(os.listdir(study_path)) if file.endswith("_2.fastq.gz")]

script_dir = os.path.dirname(__file__)

# template
template_dir = os.path.abspath(os.path.join(script_dir, "json_templates"))
template_path = os.path.join(template_dir, "qc_and_assemble.json")
with open(template_path) as f:
    template = json.loads(f.read())

    # adding files to json
for r1, r2 in zip(forward, reverse):
    template["qc_and_assemble.sampleInfo"].append({"file_r1": r1, "file_r2": r2})
# adding threads
template['qc_and_assemble.thread_num'] = threads
    
print("Found samples:")
print(len(template["qc_and_assemble.sampleInfo"]))    
    
# writing input json
with open('inputs.json', 'w') as f:
    json.dump(template, f, indent=4, sort_keys=True, ensure_ascii=False)
                            
paths = {
    "config_dir" : "./cromwell-configs/kneaddata.conf", 
    "cromwell_dir" : "../cromwell/cromwell-78.jar", 
    "wdl_dir" : "./wdl/qc_and_assemble.wdl",
    "output_dir" : "./json_templates/output_options.json"
}

for path in paths.keys():
    paths[path] = os.path.abspath(os.path.join(script_dir, paths[path]))

os.system("""java -Dconfig.file={0} -jar {1} run {2} -o {3} -i inputs.json > log.txt""".format(*paths.values()))