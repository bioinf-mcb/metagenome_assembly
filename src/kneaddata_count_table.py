import os 
import json
import sys 

from _utils import (
    modify_output_config,
    read_evaluate_log
)

import argparse

# Command line argyments
parser = argparse.ArgumentParser(description='Generate read count table post KneadData QC')
parser.add_argument('-i','--input_folder', help='The directory with KneadData logs', required=True)
parser.add_argument('-o','--output_folder', help='The directory for the output', required=True)
args = vars(parser.parse_args())

system_folder = os.path.join(args["output_folder"], "system")

logs  = [os.path.join(args["input_folder"], file) for file in sorted(os.listdir(args["input_folder"])) if file.endswith(".log")]

if not logs:
    raise FileNotFoundError("No .log files found")
    
# json template
read_table_input = {"read_table.logs" : logs}
# writing input json
os.makedirs(args["output_folder"], exist_ok=True)
inputs_path = os.path.join(args["output_folder"], 'input_logs.json')

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

modify_output_config(paths["output_dir"], args["output_folder"], system_folder)

log_path = os.path.join(system_folder, "log.txt")
# pass everything to a shell command
cmd = """java -Dconfig.file={0} -jar {1} run {2} -o {3} -i {4} > {5}""".format(*paths.values(), inputs_path, log_path)
os.system(cmd)

read_evaluate_log(log_path)