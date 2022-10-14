from distutils.command.config import config
import os 
import json
import sys 

from _utils import (
    modify_output_config,
    read_json_config,
    check_inputs_not_empty,
    create_directory,
    read_evaluate_log,
    start_workflow
)

import argparse

# Command line argyments
parser = argparse.ArgumentParser(description='Generate read count table post KneadData QC')
parser.add_argument('-i','--input_folder', help='The directory with KneadData logs', required=True)
parser.add_argument('-o','--output_folder', help='The directory for the output', required=True)
args = vars(parser.parse_args())

system_folder = os.path.join(args["output_folder"], "system")
script_dir = os.path.dirname(__file__)
config = read_json_config(os.path.join(script_dir, "config.json"))

logs  = [os.path.join(args["input_folder"], file) for file in sorted(os.listdir(args["input_folder"])) if file.endswith(".log")]

check_inputs_not_empty({"logs" : logs})
    
# json template
read_table_input = {"read_table.logs" : logs}
# writing input json
create_directory(args["output_folder"])
create_directory(system_folder)

inputs_path = os.path.join(system_folder, 'input_logs.json')

with open(inputs_path, 'w') as f:
    json.dump(read_table_input, f, indent=4, sort_keys=True, ensure_ascii=False)

script_name = os.path.basename(__file__).split(".")[0]

paths = {
    "config_path" : config["db_mount_config"], 
    "cromwell_path" : config["cromwell_path"], 
    "wdl_path" : config["wdls"][script_name],
    "output_config_path" : config["output_config_path"]
}

# creating absolute paths
for path in paths.keys():
    paths[path] = os.path.abspath(os.path.join(script_dir, paths[path]))

modify_output_config(paths["output_dir"], args["output_folder"], system_folder)

# starting workflow
log_path = start_workflow(paths, inputs_path, system_folder)

read_evaluate_log(log_path)