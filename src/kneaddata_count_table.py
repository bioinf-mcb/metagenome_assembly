import os 
import json 
import sys
from _utils import (
    modify_output_config
)

import argparse

# Command line argyments
parser = argparse.ArgumentParser(description='Generate read count table post KneadData QC')
parser.add_argument('-i','--input', help='The directory with KneadData logs', required=True)
parser.add_argument('-o','--output_dir', help='The directory for the output', required=True)
args = vars(parser.parse_args())

study_path = args["inputs"]
output_path = args["output_dir"]

logs  = [os.path.join(study_path, file) for file in sorted(os.listdir(study_path)) if file.endswith(".log")]

if not logs:
    raise FileNotFoundError("No .log files found")
    
# json template
read_table_input = {"read_table.logs" : logs}
# writing input json
os.makedirs(output_path, exist_ok=True)
inputs_path = os.path.join(output_path, 'input_logs.json')

with open(inputs_path, 'w') as f:
    json.dump(read_table_input, f, indent=4, sort_keys=True, ensure_ascii=False)

    
script_dir = os.path.dirname(__file__)

paths = {
    "config_dir" : "./cromwell_configs/kneaddata.conf", 
    "cromwell_dir" : "../cromwell/cromwell-78.jar", 
    "wdl_dir" : "./wdl/util_kneaddata.wdl",
    "output_dir" : "json_templates/output_options.json"
}

# creating absolute paths
for path in paths.keys():
    paths[path] = os.path.abspath(os.path.join(script_dir, paths[path]))

modify_output_config(paths["output_dir"], output_path)

log_path = os.path.join(output_path, "log.txt")
# pass everything to a shell command
os.system("""java -Dconfig.file={0} -jar {1} run {2} -o {3} -i {4} > {5}""".format(*paths.values(), inputs_path, log_path))