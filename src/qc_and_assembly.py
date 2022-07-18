import os 
import json 
import re

from rich.console import Console
console = Console()

from _utils import (
    modify_output_config,
    modify_concurrency_config
)

import argparse

## TODO test for single end reads
parser = argparse.ArgumentParser(description='Quality control and assembly of contigs',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
## TODO add all arguments from wdl script
parser.add_argument('-i','--input_folder', help='The directory with raw reads in .fastq or fastq.gz\
                    format', required=True)
parser.add_argument('-t','--threads', help='Number of threads to use', default=1, type=int, required=False)
parser.add_argument('-o','--output_dir', help='The directory for the output', required=True)
parser.add_argument('-c','--concurrent_jobs', help='Number of jobs to run in parallel', 
                    type=int, default=1, required=False)
parser.add_argument('-bt2_index','--bowtie2_index', help='Path to Bowtie2 index', required=True)

args = vars(parser.parse_args())

study_path = os.path.abspath(args["input_folder"])
threads = args["threads"]
output_path = args["output_dir"]
system_path = os.path.join(output_path, "system")

# getting sorted lists of forward and reverse reads from a folder
forward, reverse = [os.path.join(study_path, file) for file in sorted(os.listdir(study_path)) if file.endswith("_1.fastq.gz")], \
                   [os.path.join(study_path, file) for file in sorted(os.listdir(study_path)) if file.endswith("_2.fastq.gz")]

script_dir = os.path.dirname(__file__)

## TODO modify template to include all arguments
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

# creating output directory
os.makedirs(output_path, exist_ok=True)
os.makedirs(system_path, exist_ok=True)

# writing input json
inputs_path = os.path.join(system_path, 'inputs.json')
with open(inputs_path, 'w') as f:
    json.dump(template, f, indent=4, sort_keys=True, ensure_ascii=False)

    
script_dir = os.path.dirname(__file__)

log_path = os.path.join(system_path, "log.txt")

paths = {
    "config_dir" : "./cromwell_configs/kneaddata.conf", 
    "cromwell_dir" : "../cromwell/cromwell-81.jar", 
    "wdl_dir" : "./wdl/qc_and_assemble.wdl",
    "output_dir" : "./json_templates/output_options.json"
}

for path in paths.keys():
    paths[path] = os.path.abspath(os.path.join(script_dir, paths[path]))

paths["output_dir"] = modify_output_config(paths["output_dir"], system_path)
paths["config_dir"] = modify_concurrency_config(paths["config_dir"], system_path, 
                                                args["concurrent_jobs"], os.path.abspath(args["bowtie2_index"]))

os.system("""java -Dconfig.file={0} -jar {1} run {2} -o {3} -i {4} > {5}""".format(*paths.values(), inputs_path, log_path))

with open(log_path) as f:
    log = f.read()

if "workflow finished with status 'Succeeded'" in log:
    console.log("Workflow finished successfully", style="green")
else:
    console.log("Workflow failed, check the log file", style="red")